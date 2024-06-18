from astal import celery

if __name__ == '__main__':
    celery.start()


# komanda za pokretanje celery worker-a:
#! celery -A celery_worker.celery worker --loglevel=info