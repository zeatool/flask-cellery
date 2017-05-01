# Flask+Celery XML parser

Тестовая задача, производит парсинг XML файла в асинхронном режиме.

Формат XML файла:

```xml
<items>
    <item>
        <id>1</id>
    </item>
    <item>
        <id>2</id>
        <parentId>1</parentId>
    </item>
    ...
</items>
```

Чтобы запустить задачу необходимо выполнить:
```sh
docker-compose 
```