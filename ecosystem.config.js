module.exports = {
  apps: [{
    name: 'telegram-search-bot',
    script: 'main.py',
    interpreter: './venv/bin/python',
    cwd: '/root/ChineseSearch',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      NODE_ENV: 'production'
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true,
    merge_logs: true,
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
  }]
};

