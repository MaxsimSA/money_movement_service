from django.db import models
from django.core.validators import MinValueValidator
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from datetime import date

class Status(models.Model):
    
    #Модель для статусов операций
    
    BUSINESS = 'business'
    PERSONAL = 'personal'
    TAX = 'tax'
    
    STATUS_CHOICES = [
        (BUSINESS, 'Бизнес'),
        (PERSONAL, 'Личное'),
        (TAX, 'Налог'),
    ]
    
    code = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        unique=True,
        verbose_name="Код статуса",
        blank=True,  # Разрешаем пустые значения для кастомных статусов
        null=True
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name="Название статуса",
        unique=True  # Запрещаем дублирование названий
    )
    
    is_custom = models.BooleanField(
        default=False,
        verbose_name="Пользовательский статус"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Статус"
        verbose_name_plural = "Статусы"
        ordering = ['name']

    @classmethod
    def create_default_statuses(cls):
        for code, name in cls.STATUS_CHOICES:
            if not cls.objects.filter(code=code).exists():
                cls.objects.create(code=code, name=name, is_custom=False)

class Type(models.Model):
    
    #Модель для типов операций
    
    INCOME = 'income'
    EXPENSE = 'expense'
    
    TYPE_CHOICES = [
        (INCOME, 'Пополнение'),
        (EXPENSE, 'Списание'),
    ]
    
    code = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        unique=True,
        verbose_name="Код типа",
        blank=True,
        null=True
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name="Название типа",
        unique=True
    )
    
    is_custom = models.BooleanField(
        default=False,
        verbose_name="Пользовательский тип"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тип операции"
        verbose_name_plural = "Типы операций"
        ordering = ['name']

    @classmethod
    def create_default_types(cls):
        for code, name in cls.TYPE_CHOICES:
            if not cls.objects.filter(code=code).exists():
                cls.objects.create(code=code, name=name, is_custom=False)

class Category(models.Model):
    
    #Модель категорий операций
    
    type = models.ForeignKey(
        Type,
        on_delete=models.PROTECT,
        verbose_name="Тип операции",
        related_name='categories'
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name="Название категории"
    )

    def __str__(self):
        return f"{self.type.name} - {self.name}"

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        # Запрещаем дублирование названий в рамках одного типа
        unique_together = ('type', 'name')
        ordering = ['type__name', 'name']

class SubCategory(models.Model):
    
    #Модель подкатегорий операций
    
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name="Категория",
        related_name='subcategories'
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name="Название подкатегории"
    )

    def __str__(self):
        return f"{self.category.name} - {self.name}"

    class Meta:
        verbose_name = "Подкатегория"
        verbose_name_plural = "Подкатегории"
        # Запрещаем дублирование названий в рамках одной категории
        unique_together = ('category', 'name')
        ordering = ['category__name', 'name']

class MoneyMovement(models.Model):

    Основная модель для учета движения денежных средств
    
    date = models.DateField(
        default=date.today,
        verbose_name="Дата операции"
    )
    
    status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        verbose_name="Статус операции"
    )
    
    type = models.ForeignKey(
        Type,
        on_delete=models.PROTECT,
        verbose_name="Тип операции"
    )
    
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        verbose_name="Категория"
    )
    

    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.PROTECT,
        verbose_name="Подкатегория",
        blank=True,
        null=True
    )
    
    amount = models.DecimalField(
        verbose_name="Сумма (руб)",
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]  # Минимальное значение 0.01
    )
    
    comment = models.TextField(
        verbose_name="Комментарий",
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.date}: {self.type.name} {self.amount}р ({self.status.name})"

    class Meta:
        verbose_name = "Движение денежных средств"
        verbose_name_plural = "Движения денежных средств"
        ordering = ["-date"]  # Сортировка по дате (новые сверху)

    def clean(self):
        
        from django.core.exceptions import ValidationError
        
        if self.category.type_id != self.type_id:
            raise ValidationError(
                f"Категория '{self.category.name}' не принадлежит типу '{self.type.name}'"
            )
        
        if self.subcategory and self.subcategory.category_id != self.category_id:
            raise ValidationError(
                f"Подкатегория '{self.subcategory.name}' не принадлежит категории '{self.category.name}'"
            )

@receiver(post_migrate)
def create_initial_data(sender, **kwargs):
    if sender.name == 'money_movement_service':
        Status.create_default_statuses()
        Type.create_default_types()
        
        income_type = Type.objects.get(code=Type.INCOME)
        expense_type = Type.objects.get(code=Type.EXPENSE)
        
        infrastructure = Category.objects.get_or_create(
            name='Инфраструктура',
            type=expense_type
        )[0]
        
        SubCategory.objects.get_or_create(
            name='VPS',
            category=infrastructure
        )
        SubCategory.objects.get_or_create(
            name='Proxy',
            category=infrastructure
        )
        
        marketing = Category.objects.get_or_create(
            name='Маркетинг',
            type=expense_type
        )[0]
        
        SubCategory.objects.get_or_create(
            name='Farpost',
            category=marketing
        )
        SubCategory.objects.get_or_create(
            name='Avito',
            category=marketing
        )
        
        income_category = Category.objects.get_or_create(
            name='Поступления',
            type=income_type
        )[0]
        
        SubCategory.objects.get_or_create(
            name='Продажи',
            category=income_category
        )
