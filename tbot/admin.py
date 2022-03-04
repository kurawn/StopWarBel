from django.contrib import admin
from .models import *


from django.contrib import admin
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import *


class AdminImageWidget(AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        output = []

        if value and getattr(value, "url", None):
            image_url = value.url
            file_name = str(value)

            output.append(
                f' <a href="{image_url}" target="_blank">'
                f'  <img src="{image_url}" alt="{file_name}" height="300" '
                f'style="object-fit: cover;"/> </a>'
            )
        # output.append(super(AdminFileWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))


class AdminVideoWidget(AdminFileWidget):
    def render(self, name, value, attrs=None, renderer=None):
        output = []

        if value and getattr(value, "url", None):
            url = value.url

            output.append(
                f'<video height="300px" controls>'
                f'<source src="{url}" type="video/mp4">'
                f'</video>')

        # output.append(super(AdminFileWidget, self).render(name, value, attrs, renderer))
        return mark_safe(u''.join(output))


class ProofInlines(admin.TabularInline):
    model = Proof
    readonly_fields = ('date_create', 'user')
    fields = ['user', 'image', 'video', 'description', 'date_create']
    ordering = ['-date_create']
    formfield_overrides = {models.ImageField: {'widget': AdminImageWidget},
                           models.FileField: {'widget': AdminVideoWidget}}
    extra = 0


@admin.register(User)
class ModelUser(admin.ModelAdmin):
    inlines = [ProofInlines,]
    list_display = ['user_id', 'name', 'username',]
    search_fields = ('user_id', 'name', 'username')


@admin.register(BotConf)
class ModelUser(admin.ModelAdmin):
    list_display = ['chat_id']