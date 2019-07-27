# Titsa-Bot

## Implementación funcionando: https://t.me/TransporteTFBot

**Bot del transporte de Tenerife**

Este bot permite a los usuarios conocer el tiempo que falta para que efectúen paso las guaguas o tranvías por las paradas indicadas. También permite marcar paradas de guaguas como favoritas, así como nombrar a dichas paradas con un nombre especificado por el usuario. 

**¿Cómo implementarlo por mi cuenta?**

Instalar las dependencias (Python-telegram-bot), así como cumplimentar las settings del token de Titsa, de telegram y el chat id del admin del bot (Para emitir avisos a los usuarios):

`bot_config.ini`:

```ini
[TITSA]
idApp = *****************

[TELEGRAM]
token = **************

[ADMIN]
chatId = ********
```
