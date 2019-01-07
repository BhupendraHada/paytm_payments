from celery.task.base import task, current_app, Task
from django.conf import settings

class CeleryTask(Task):

    def apply_async(
        self,
        args=None,
        kwargs=None,
        task_id=None,
        producer=None,
        link=None,
        link_error=None,
        **options
    ):
        # IF sandbox is true do not publish message in queue
        # IF sandbox is False push to odoo.
        if not settings.SANDBOX:
            super(CeleryTask, self).apply_async(
                args,
                kwargs,
                task_id,
                producer,
                link,
                link_error,
                **options
            )
        return True


def task(*args, **kwargs):
    """Deprecated decorator, please use :func:`celery.task`."""
    return current_app.task(
        *args,
        **dict(
            {
                'accept_magic_kwargs': False,
                'base': CeleryTask
            },
            **kwargs
        )
    )
