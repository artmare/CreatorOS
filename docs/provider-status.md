# Provider Status

The product runs locally without provider secrets. Provider-backed behavior turns on through environment variables:

- Supabase Auth: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_JWT_SECRET`
- OpenAI: `OPENAI_API_KEY`
- Telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`
- YouTube: `YOUTUBE_API_KEY`
- Lemon Squeezy: `LEMONSQUEEZY_API_KEY`, `LEMONSQUEEZY_STORE_ID`, variant IDs, webhook secret

Current adapter behavior:

- Missing OpenAI key: agent services return deterministic CreatorOS-quality mock output.
- Missing Telegram token: webhook handler returns what it would reply.
- Missing YouTube key: connector returns mocked summaries with `enabled: false`.
- Missing Lemon Squeezy key: checkout route returns plan/provider metadata with `enabled: false`.
