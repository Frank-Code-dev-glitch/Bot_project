# bot/models.py - Add these updates to your existing models
from django.db import models
import uuid

class Customer(models.Model):
    PLATFORM_CHOICES = [
        ('telegram', 'Telegram'),
        ('whatsapp', 'WhatsApp'),
    ]
    
    LANGUAGE_CHOICES = [
        ('sheng', 'Sheng'),
        ('swenglish', 'Swenglish'), 
        ('english', 'English'),
    ]
    
    # Platform identification
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='telegram')
    platform_user_id = models.CharField(max_length=100, unique=True)  # Telegram ID or WhatsApp number
    
    # Customer information
    phone_number = models.CharField(max_length=15, blank=True)
    name = models.CharField(max_length=100, blank=True)
    
    # Language and preferences
    preferred_language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='swenglish')
    
    # Tracking
    first_interaction = models.DateTimeField(auto_now_add=True)
    last_interaction = models.DateTimeField(auto_now=True)
    total_interactions = models.IntegerField(default=0)
    
    # Platform-specific data
    telegram_username = models.CharField(max_length=100, blank=True)
    whatsapp_name = models.CharField(max_length=100, blank=True)
    
    class Meta:
        unique_together = ['platform', 'platform_user_id']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
    
    def __str__(self):
        return f"{self.name or 'Unknown'} ({self.platform}: {self.platform_user_id})"
    
    def get_display_id(self):
        """Get display-friendly user ID"""
        if self.platform == 'whatsapp':
            return f"whatsapp:{self.platform_user_id[-4:]}"  # Last 4 digits for privacy
        return f"telegram:{self.platform_user_id}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    # Platform and customer
    platform = models.CharField(max_length=20, choices=Customer.PLATFORM_CHOICES)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='appointments')
    
    # Appointment details
    service_type = models.CharField(max_length=100)
    scheduled_date = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Financials
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Platform-specific references
    telegram_message_id = models.CharField(max_length=50, blank=True)
    whatsapp_message_id = models.CharField(max_length=50, blank=True)
    mpesa_checkout_id = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_date']
        indexes = [
            models.Index(fields=['platform', 'customer']),
            models.Index(fields=['scheduled_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.customer.get_display_id()} - {self.service_type} - {self.scheduled_date.strftime('%Y-%m-%d %H:%M')}"

class Conversation(models.Model):
    """Track conversations across platforms"""
    PLATFORM_CHOICES = [
        ('telegram', 'Telegram'),
        ('whatsapp', 'WhatsApp'),
    ]
    
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    platform_user_id = models.CharField(max_length=100)
    
    # Message content
    user_message = models.TextField()
    bot_response = models.TextField()
    
    # Context
    intent = models.CharField(max_length=100, blank=True)
    confidence = models.FloatField(default=0.0)
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    message_id = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['platform', 'platform_user_id']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.platform}:{self.platform_user_id} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

# Add this function to create/update customers
def get_or_create_customer(platform, platform_user_id, **kwargs):
    """Get or create customer with platform support"""
    customer, created = Customer.objects.get_or_create(
        platform=platform,
        platform_user_id=platform_user_id,
        defaults=kwargs
    )
    
    if not created:
        # Update fields if provided
        for key, value in kwargs.items():
            if hasattr(customer, key):
                setattr(customer, key, value)
        customer.save()
    
    return customer, created