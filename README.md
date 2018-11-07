# Discord-Billing-License-Bot
Simple Discord bot that will verify [WHMCS](https://www.whmcs.com/members/verifydomain.php) and [Blesta](https://account.blesta.com/client/plugin/license_verify/) billing panel licenses

## Prerequisites

* Python 3 (tested with v3.6.6, should work for 3.5+)
* Admin permissions on Discord server
* No bot permissions are required

## Instructions

### Invite Hosted Bot

I am hosting this bot on a server, thus it can be invited to your server easily without the need to host the bot yourself.

1. Open the invite link below to start the process of adding the bot to your Discord server
  https://discordapp.com/oauth2/authorize?&client_id=480073510790889472&scope=bot&permissions=0
2. Select the server you wish to invite the bot to
3. Hit 'Authorize' and the bot will be added

### Self-Hosted Bot

1. Follow [these directions](https://discordpy.readthedocs.io/en/rewrite/discord.html) in order to register the bot and create a token
2. Replace the token at the top of the _licensebot.py_ file with your generated token
3. Invite the bot to your server

_The bot does not require any special permissions_

## License
```
            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
                    Version 2, December 2004

 Copyright (C) 2018 Mason Rowe <mason@rowe.sh>

 Everyone is permitted to copy and distribute verbatim or modified
 copies of this license document, and changing it is allowed as long
 as the name is changed.

            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

  0. You just DO WHAT THE FUCK YOU WANT TO.
```