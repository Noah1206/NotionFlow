-- NotionFlow 결제 시스템 데이터베이스 스키마
-- SupaBase PostgreSQL용

-- 1. 구독 플랜 테이블
CREATE TABLE IF NOT EXISTS subscription_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_name VARCHAR(50) NOT NULL,
    plan_code VARCHAR(20) UNIQUE NOT NULL,
    price_monthly INTEGER NOT NULL, -- 원화 기준 (원)
    price_yearly INTEGER NOT NULL,  -- 원화 기준 (원)
    features JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 사용자 구독 정보 테이블
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL, -- users 테이블과 연결
    plan_id UUID REFERENCES subscription_plans(id),
    status VARCHAR(20) NOT NULL DEFAULT 'trial', -- trial, active, cancelled, expired
    billing_cycle VARCHAR(10) NOT NULL, -- monthly, yearly
    trial_ends_at TIMESTAMP WITH TIME ZONE,
    current_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    current_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    auto_renew BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 결제 내역 테이블
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    subscription_id UUID REFERENCES user_subscriptions(id),
    payment_key VARCHAR(200) NOT NULL, -- 토스페이먼츠 결제 키
    order_id VARCHAR(100) NOT NULL UNIQUE, -- 주문 번호
    amount INTEGER NOT NULL, -- 결제 금액 (원)
    status VARCHAR(20) NOT NULL, -- pending, completed, failed, cancelled, refunded
    payment_method VARCHAR(50), -- 결제 수단
    payment_provider VARCHAR(50) DEFAULT 'toss', -- 결제 제공업체
    provider_transaction_id VARCHAR(200), -- 제공업체 거래 ID
    receipt_url TEXT, -- 영수증 URL
    failure_reason TEXT, -- 실패 사유
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. 청구 주소 테이블 (선택사항)
CREATE TABLE IF NOT EXISTS billing_addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    recipient_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    postal_code VARCHAR(10),
    address VARCHAR(200),
    address_detail VARCHAR(100),
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. 결제 웹훅 로그 테이블
CREATE TABLE IF NOT EXISTS payment_webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    payment_key VARCHAR(200),
    order_id VARCHAR(100),
    webhook_data JSONB NOT NULL,
    processed BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_billing_addresses_user_id ON billing_addresses(user_id);

-- RLS (Row Level Security) 정책
ALTER TABLE user_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_addresses ENABLE ROW LEVEL SECURITY;

-- 사용자는 자신의 구독 정보만 볼 수 있음
CREATE POLICY "Users can view own subscriptions" ON user_subscriptions
    FOR SELECT USING (auth.uid()::text = user_id::text);

-- 사용자는 자신의 결제 내역만 볼 수 있음
CREATE POLICY "Users can view own payments" ON payments
    FOR SELECT USING (auth.uid()::text = user_id::text);

-- 사용자는 자신의 청구 주소만 관리할 수 있음
CREATE POLICY "Users can manage own billing addresses" ON billing_addresses
    FOR ALL USING (auth.uid()::text = user_id::text);

-- 기본 구독 플랜 데이터 삽입
INSERT INTO subscription_plans (plan_name, plan_code, price_monthly, price_yearly, features) VALUES
('캘린더 통합', 'CALENDAR_INTEGRATION', 12000, 108000, 
 '{
   "features": [
     "무제한 캘린더 동기화",
     "모든 플랫폼 연결 (Google, Apple, Notion, Outlook, Slack)",
     "실시간 동기화",
     "고급 대시보드 & 분석", 
     "팀 협업 도구",
     "우선 고객 지원",
     "자동 백업 & 복구"
   ],
   "limits": {
     "calendars": "unlimited",
     "sync_frequency": "real-time",
     "platforms": "all"
   }
 }'::jsonb)
ON CONFLICT (plan_code) DO NOTHING;

-- 업데이트 트리거 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 업데이트 트리거 생성
CREATE TRIGGER update_subscription_plans_updated_at BEFORE UPDATE ON subscription_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_subscriptions_updated_at BEFORE UPDATE ON user_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payments_updated_at BEFORE UPDATE ON payments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_billing_addresses_updated_at BEFORE UPDATE ON billing_addresses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();