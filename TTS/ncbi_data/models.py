from django.db import models
import json
import logging

logger = logging.getLogger('ncbi_data')

# Create your models here.

class NCBIData(models.Model):
    db = models.CharField(max_length=50)
    query = models.CharField(max_length=255)
    data = models.TextField()  # Changed from JSONField to TextField
    translation_term = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.db} - {self.query}"

    class Meta:
        unique_together = ('db', 'query')
        indexes = [
            models.Index(fields=['db', 'query']),
        ]

    def set_data(self, data):
        self.data = json.dumps(data)
        logger.debug(f"Data serialized for db: {self.db}, query: {self.query}")
        print(f"Data serialized for db: {self.db}, query: {self.query}")

    def get_data(self):
        logger.debug(f"Data deserialized for db: {self.db}, query: {self.query}")
        print(f"Data deserialized for db: {self.db}, query: {self.query}")
        return json.loads(self.data)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            logger.info(f"New NCBIData object created: db={self.db}, query={self.query}")
            print(f"New NCBIData object created: db={self.db}, query={self.query}")
        else:
            logger.info(f"NCBIData object updated: db={self.db}, query={self.query}")
            print(f"NCBIData object updated: db={self.db}, query={self.query}")
