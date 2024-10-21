DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'naresh_tts',
        'USER': 'Naresh',
        'PASSWORD': '4ev@nnW*CaQUQU4',
        'HOST': 'mysql-naresh.alwaysdata.net',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}
