-- Этап 1: таблица избранных рецептов
-- Выполните в Supabase: SQL Editor → New query → Run

CREATE TABLE IF NOT EXISTS favorites (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, recipe_id)
);

CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_favorites_recipe_id ON favorites(recipe_id);

-- Если включён RLS — разрешить anon-ключу (как у остальных таблиц бота)
ALTER TABLE favorites ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all for favorites"
    ON favorites
    FOR ALL
    USING (true)
    WITH CHECK (true);
