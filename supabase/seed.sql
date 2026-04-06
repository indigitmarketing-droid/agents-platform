-- seed.sql
INSERT INTO agents (id, status) VALUES
    ('scraping', 'offline'),
    ('setting', 'offline'),
    ('builder', 'offline')
ON CONFLICT (id) DO NOTHING;
