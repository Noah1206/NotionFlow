-- 초대링크 테이블 생성
CREATE TABLE IF NOT EXISTS public.invite_links (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    invite_code text NOT NULL UNIQUE,
    inviter_id text NOT NULL,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now(),
    expires_at timestamp with time zone,
    used_count integer DEFAULT 0,
    max_uses integer DEFAULT NULL,
    CONSTRAINT invite_links_pkey PRIMARY KEY (id)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_invite_links_code ON public.invite_links(invite_code);
CREATE INDEX IF NOT EXISTS idx_invite_links_inviter ON public.invite_links(inviter_id);
CREATE INDEX IF NOT EXISTS idx_invite_links_active ON public.invite_links(is_active);

-- RLS 정책 설정
ALTER TABLE public.invite_links ENABLE ROW LEVEL SECURITY;

-- 사용자는 자신의 초대링크만 볼 수 있음
CREATE POLICY "Users can view own invite links" ON public.invite_links
    FOR SELECT USING (inviter_id = auth.uid()::text);

-- 사용자는 자신의 초대링크만 생성할 수 있음
CREATE POLICY "Users can create own invite links" ON public.invite_links
    FOR INSERT WITH CHECK (inviter_id = auth.uid()::text);

-- 사용자는 자신의 초대링크만 업데이트할 수 있음
CREATE POLICY "Users can update own invite links" ON public.invite_links
    FOR UPDATE USING (inviter_id = auth.uid()::text);

-- 서비스 역할은 모든 접근 가능
CREATE POLICY "Service role full access" ON public.invite_links
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 초대링크 사용 내역 테이블
CREATE TABLE IF NOT EXISTS public.invite_link_usage (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    invite_link_id uuid NOT NULL,
    used_by_id text,
    used_at timestamp with time zone DEFAULT now(),
    ip_address text,
    user_agent text,
    CONSTRAINT invite_link_usage_pkey PRIMARY KEY (id),
    CONSTRAINT invite_link_usage_link_fkey FOREIGN KEY (invite_link_id) REFERENCES public.invite_links(id) ON DELETE CASCADE
);

-- 사용 내역 인덱스
CREATE INDEX IF NOT EXISTS idx_invite_usage_link ON public.invite_link_usage(invite_link_id);
CREATE INDEX IF NOT EXISTS idx_invite_usage_user ON public.invite_link_usage(used_by_id);