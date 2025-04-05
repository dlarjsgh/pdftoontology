def verify_user(token: str):
    # 👉 Supabase 검증 없이 그냥 통과
    print(f"[TEST MODE] 받은 토큰: {token}")
    return {"email": "test@example.com"}
