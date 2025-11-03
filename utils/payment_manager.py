"""
🔐 NodeFlow Payment Management System
토스페이먼츠 연동 및 구독 관리 시스템
"""

import os
import json
import uuid
import hashlib
import base64
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import requests
from utils.config import config

class PaymentManager:
    """결제 관리 시스템"""
    
    def __init__(self):
        self.supabase = config.supabase_client
        self.toss_secret_key = os.getenv('TOSS_SECRET_KEY')
        self.toss_client_key = os.getenv('TOSS_CLIENT_KEY') 
        self.toss_api_url = 'https://api.tosspayments.com/v1/payments'
        
        # 테스트 모드 여부
        self.is_test_mode = os.getenv('FLASK_ENV') != 'production'
        
        # 플랜 정보
        self.plans = {
            'CALENDAR_INTEGRATION': {
                'monthly_price': 12000,
                'yearly_price': 108000,
                'trial_days': 14
            }
        }
    
    def create_order(self, user_id: str, plan_code: str, billing_cycle: str, 
                    customer_email: str, customer_name: str) -> Dict[str, Any]:
        """주문 생성"""
        try:
            # 주문 ID 생성
            order_id = self._generate_order_id()
            
            # 플랜 정보 조회
            plan = self.plans.get(plan_code, self.plans['CALENDAR_INTEGRATION'])
            amount = plan['yearly_price'] if billing_cycle == 'yearly' else plan['monthly_price']
            
            # 체험 종료일 계산
            trial_end_date = datetime.now() + timedelta(days=plan['trial_days'])
            
            # 구독 시작일 (체험 종료 후)
            subscription_start = trial_end_date
            
            # 구독 종료일 계산
            if billing_cycle == 'yearly':
                subscription_end = subscription_start + timedelta(days=365)
            else:
                subscription_end = subscription_start + timedelta(days=30)
            
            # SupaBase에 주문 정보 저장
            order_data = {
                'user_id': user_id,
                'order_id': order_id,
                'plan_code': plan_code,
                'billing_cycle': billing_cycle,
                'amount': amount,
                'status': 'pending',
                'customer_email': customer_email,
                'customer_name': customer_name,
                'trial_ends_at': trial_end_date.isoformat(),
                'subscription_start': subscription_start.isoformat(),
                'subscription_end': subscription_end.isoformat(),
                'created_at': datetime.now().isoformat()
            }
            
            # payments 테이블에 저장
            result = self.supabase.table('payments').insert(order_data).execute()
            
            if result.data:
                return {
                    'success': True,
                    'order_id': order_id,
                    'amount': amount,
                    'trial_end_date': trial_end_date,
                    'message': '주문이 성공적으로 생성되었습니다.'
                }
            else:
                raise Exception('주문 정보 저장에 실패했습니다.')
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': '주문 생성 중 오류가 발생했습니다.'
            }
    
    def verify_payment(self, payment_key: str, order_id: str, amount: int) -> Dict[str, Any]:
        """토스페이먼츠 결제 검증"""
        try:
            # 토스페이먼츠 API로 결제 승인 요청
            auth_string = base64.b64encode(f"{self.toss_secret_key}:".encode()).decode()
            
            headers = {
                'Authorization': f'Basic {auth_string}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'paymentKey': payment_key,
                'orderId': order_id,
                'amount': amount
            }
            
            response = requests.post(
                f'{self.toss_api_url}/confirm',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                payment_data = response.json()
                
                # 결제 성공 시 DB 업데이트
                update_result = self._update_payment_success(payment_key, order_id, payment_data)
                
                if update_result['success']:
                    # 구독 활성화
                    subscription_result = self._activate_subscription(order_id)
                    
                    return {
                        'success': True,
                        'payment_data': payment_data,
                        'subscription': subscription_result,
                        'message': '결제가 성공적으로 완료되었습니다.'
                    }
                else:
                    return update_result
                    
            else:
                error_data = response.json() if response.content else {}
                return {
                    'success': False,
                    'error': error_data,
                    'message': '결제 승인에 실패했습니다.'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': '결제 검증 중 오류가 발생했습니다.'
            }
    
    def cancel_payment(self, payment_key: str, cancel_reason: str) -> Dict[str, Any]:
        """결제 취소"""
        try:
            auth_string = base64.b64encode(f"{self.toss_secret_key}:".encode()).decode()
            
            headers = {
                'Authorization': f'Basic {auth_string}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'cancelReason': cancel_reason
            }
            
            response = requests.post(
                f'{self.toss_api_url}/{payment_key}/cancel',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                cancel_data = response.json()
                
                # DB에서 결제 상태 업데이트
                self.supabase.table('payments').update({
                    'status': 'cancelled',
                    'failure_reason': cancel_reason,
                    'updated_at': datetime.now().isoformat()
                }).eq('payment_key', payment_key).execute()
                
                return {
                    'success': True,
                    'cancel_data': cancel_data,
                    'message': '결제가 성공적으로 취소되었습니다.'
                }
            else:
                error_data = response.json() if response.content else {}
                return {
                    'success': False,
                    'error': error_data,
                    'message': '결제 취소에 실패했습니다.'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': '결제 취소 중 오류가 발생했습니다.'
            }
    
    def get_user_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """사용자 구독 정보 조회 (모든 상태 포함)"""
        try:
            # 가장 최근 구독 정보 조회 (취소되지 않은 것 우선)
            result = self.supabase.table('user_subscriptions').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            
            if result.data:
                # 활성 상태(trial, active) 구독이 있으면 우선 반환
                for subscription in result.data:
                    if subscription['status'] in ['trial', 'active']:
                        return subscription
                
                # 활성 구독이 없으면 가장 최근 구독 반환
                return result.data[0]
            
            return None
            
        except Exception as e:
            print(f"구독 정보 조회 오류: {e}")
            return None
    
    def get_payment_history(self, user_id: str) -> list:
        """사용자 결제 내역 조회"""
        try:
            result = self.supabase.table('payments').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"결제 내역 조회 오류: {e}")
            return []
    
    def _generate_order_id(self) -> str:
        """주문 ID 생성"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_id = str(uuid.uuid4()).replace('-', '')[:8]
        return f"NF_{timestamp}_{random_id}"
    
    def _update_payment_success(self, payment_key: str, order_id: str, payment_data: Dict) -> Dict[str, Any]:
        """결제 성공 시 DB 업데이트"""
        try:
            update_data = {
                'payment_key': payment_key,
                'status': 'completed',
                'payment_method': payment_data.get('method'),
                'provider_transaction_id': payment_data.get('transactionKey'),
                'receipt_url': payment_data.get('receipt', {}).get('url'),
                'approved_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('payments').update(update_data).eq('order_id', order_id).execute()
            
            if result.data:
                return {
                    'success': True,
                    'message': '결제 정보가 업데이트되었습니다.'
                }
            else:
                raise Exception('결제 정보 업데이트에 실패했습니다.')
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': '결제 정보 업데이트 중 오류가 발생했습니다.'
            }
    
    def _activate_subscription(self, order_id: str) -> Dict[str, Any]:
        """구독 활성화"""
        try:
            # 주문 정보 조회
            payment_result = self.supabase.table('payments').select('*').eq('order_id', order_id).execute()
            
            if not payment_result.data:
                raise Exception('주문 정보를 찾을 수 없습니다.')
            
            payment_info = payment_result.data[0]
            
            # 플랜 정보 조회
            plan_result = self.supabase.table('subscription_plans').select('*').eq('plan_code', payment_info['plan_code']).execute()
            
            if not plan_result.data:
                raise Exception('플랜 정보를 찾을 수 없습니다.')
            
            plan_info = plan_result.data[0]
            
            # 구독 생성
            subscription_data = {
                'user_id': payment_info['user_id'],
                'plan_id': plan_info['id'],
                'status': 'trial',  # 체험 기간으로 시작
                'billing_cycle': payment_info['billing_cycle'],
                'trial_ends_at': payment_info['trial_ends_at'],
                'current_period_start': payment_info['subscription_start'],
                'current_period_end': payment_info['subscription_end'],
                'auto_renew': True,
                'created_at': datetime.now().isoformat()
            }
            
            # 기존 구독이 있다면 비활성화
            self.supabase.table('user_subscriptions').update({
                'status': 'cancelled',
                'updated_at': datetime.now().isoformat()
            }).eq('user_id', payment_info['user_id']).execute()
            
            # 새 구독 생성
            result = self.supabase.table('user_subscriptions').insert(subscription_data).execute()
            
            if result.data:
                return {
                    'success': True,
                    'subscription_id': result.data[0]['id'],
                    'message': '구독이 활성화되었습니다.'
                }
            else:
                raise Exception('구독 생성에 실패했습니다.')
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': '구독 활성화 중 오류가 발생했습니다.'
            }
    
    def check_subscription_status(self, user_id: str) -> Dict[str, Any]:
        """구독 상태 확인 및 업데이트"""
        try:
            subscription = self.get_user_subscription(user_id)
            
            if not subscription:
                return {
                    'status': 'none',
                    'message': '활성 구독이 없습니다.'
                }
            
            now = datetime.now()
            trial_ends_at = datetime.fromisoformat(subscription['trial_ends_at'].replace('Z', '+00:00'))
            current_period_end = datetime.fromisoformat(subscription['current_period_end'].replace('Z', '+00:00'))
            
            # 체험 기간 확인
            if subscription['status'] == 'trial' and now >= trial_ends_at:
                # 체험 기간 종료 - 유료 구독으로 전환
                self.supabase.table('user_subscriptions').update({
                    'status': 'active',
                    'updated_at': datetime.now().isoformat()
                }).eq('id', subscription['id']).execute()
                
                subscription['status'] = 'active'
            
            # 구독 만료 확인
            elif subscription['status'] == 'active' and now >= current_period_end:
                if subscription['auto_renew']:
                    # 자동 갱신 로직 (실제로는 별도의 배치 작업에서 처리)
                    pass
                else:
                    # 구독 만료
                    self.supabase.table('user_subscriptions').update({
                        'status': 'expired',
                        'updated_at': datetime.now().isoformat()
                    }).eq('id', subscription['id']).execute()
                    
                    subscription['status'] = 'expired'
            
            return {
                'status': subscription['status'],
                'subscription': subscription,
                'trial_ends_at': trial_ends_at,
                'current_period_end': current_period_end,
                'message': '구독 상태가 확인되었습니다.'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'message': '구독 상태 확인 중 오류가 발생했습니다.'
            }
    
    def toggle_auto_renew(self, user_id: str) -> Dict[str, Any]:
        """자동 갱신 설정 토글"""
        try:
            # 현재 구독 정보 조회
            result = self.supabase.table('user_subscriptions').select('*').eq('user_id', user_id).neq('status', 'cancelled').execute()
            
            if not result.data:
                return {
                    'success': False,
                    'error': '활성 구독을 찾을 수 없습니다.',
                    'message': '구독 정보를 확인해주세요.'
                }
            
            subscription = result.data[0]
            new_auto_renew = not subscription['auto_renew']
            
            # 자동 갱신 상태 업데이트
            update_result = self.supabase.table('user_subscriptions').update({
                'auto_renew': new_auto_renew,
                'updated_at': datetime.now().isoformat()
            }).eq('id', subscription['id']).execute()
            
            if update_result.data:
                return {
                    'success': True,
                    'auto_renew': new_auto_renew,
                    'message': f'자동 갱신이 {"활성화" if new_auto_renew else "비활성화"}되었습니다.'
                }
            else:
                raise Exception('자동 갱신 설정 업데이트에 실패했습니다.')
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': '자동 갱신 설정 변경 중 오류가 발생했습니다.'
            }
    
    def cancel_subscription(self, user_id: str, cancel_reason: str = None) -> Dict[str, Any]:
        """구독 취소"""
        try:
            # 현재 구독 정보 조회
            result = self.supabase.table('user_subscriptions').select('*').eq('user_id', user_id).neq('status', 'cancelled').execute()
            
            if not result.data:
                return {
                    'success': False,
                    'error': '활성 구독을 찾을 수 없습니다.',
                    'message': '구독 정보를 확인해주세요.'
                }
            
            subscription = result.data[0]
            current_period_end = datetime.fromisoformat(subscription['current_period_end'].replace('Z', '+00:00'))
            
            # 구독 상태를 취소로 변경
            cancel_data = {
                'status': 'cancelled',
                'auto_renew': False,
                'cancelled_at': datetime.now().isoformat(),
                'cancel_reason': cancel_reason or '사용자 요청',
                'updated_at': datetime.now().isoformat()
            }
            
            update_result = self.supabase.table('user_subscriptions').update(cancel_data).eq('id', subscription['id']).execute()
            
            if update_result.data:
                # 취소 내역을 별도 테이블에 로깅 (선택사항)
                try:
                    self.supabase.table('subscription_cancellations').insert({
                        'user_id': user_id,
                        'subscription_id': subscription['id'],
                        'cancelled_at': datetime.now().isoformat(),
                        'cancel_reason': cancel_reason or '사용자 요청',
                        'remaining_days': max(0, (current_period_end - datetime.now()).days),
                        'created_at': datetime.now().isoformat()
                    }).execute()
                except Exception as log_error:
                    print(f"취소 로깅 실패: {log_error}")
                
                return {
                    'success': True,
                    'cancelled_at': datetime.now().isoformat(),
                    'current_period_end': current_period_end.isoformat(),
                    'message': f'구독이 취소되었습니다. {current_period_end.strftime("%Y년 %m월 %d일")}까지 서비스를 이용하실 수 있습니다.'
                }
            else:
                raise Exception('구독 취소 처리에 실패했습니다.')
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': '구독 취소 중 오류가 발생했습니다.'
            }
    
    def reactivate_subscription(self, user_id: str) -> Dict[str, Any]:
        """구독 재활성화"""
        try:
            # 취소된 구독 정보 조회
            result = self.supabase.table('user_subscriptions').select('*').eq('user_id', user_id).eq('status', 'cancelled').execute()
            
            if not result.data:
                return {
                    'success': False,
                    'error': '취소된 구독을 찾을 수 없습니다.',
                    'message': '새로운 구독을 시작해주세요.'
                }
            
            subscription = result.data[0]
            current_period_end = datetime.fromisoformat(subscription['current_period_end'].replace('Z', '+00:00'))
            
            # 구독 기간이 아직 남아있는지 확인
            if datetime.now() >= current_period_end:
                return {
                    'success': False,
                    'error': '구독 기간이 만료되었습니다.',
                    'message': '새로운 구독을 시작해주세요.'
                }
            
            # 구독 재활성화
            reactivate_data = {
                'status': 'active',
                'auto_renew': True,
                'cancelled_at': None,
                'cancel_reason': None,
                'updated_at': datetime.now().isoformat()
            }
            
            update_result = self.supabase.table('user_subscriptions').update(reactivate_data).eq('id', subscription['id']).execute()
            
            if update_result.data:
                return {
                    'success': True,
                    'reactivated_at': datetime.now().isoformat(),
                    'current_period_end': current_period_end.isoformat(),
                    'message': '구독이 재활성화되었습니다.'
                }
            else:
                raise Exception('구독 재활성화 처리에 실패했습니다.')
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': '구독 재활성화 중 오류가 발생했습니다.'
            }