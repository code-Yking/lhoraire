from django.db import models

# Create your models here.


class Tasks(models.Model):
    task_name = models.CharField(max_length=50)
    task_description = models.CharField(max_length=300)
    due_date = models.DateTimeField()
    hours_needed = models.DecimalField(decimal_places=2, max_digits=4)

    days_needed = models.DecimalField(decimal_places=2, max_digits=4)

    def __str__(self):
        return self.task_name
