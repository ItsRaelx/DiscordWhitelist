
# Minecraft Whitelist Discord Bot

This bot manages a Minecraft server's whitelist through Discord.

## Features

- Adds or removes users from the Minecraft server whitelist
- Stores whitelist in a SQLite database
- Checks if a Minecraft username is a premium account
- Deletes non-command messages from the configured channel


## Environment Variables

To run this project, you will need to add the following environment variables to your .env file or docker-compose.yml

`DISCORD_TOKEN` The token for your Discord bot.

`CHANNEL_ID` The ID of the Discord channel where commands will be accepted.

`ROLE_ID` The ID of the Discord role allowed to add/remove any user from the whitelist.

`RCON_IP` The IP address of your Minecraft server.

`RCON_PORT` The port of your Minecraft server for RCON.

`RCON_PASSWORD` The RCON password of your Minecraft server.

## Deployment

To run this project add all variables to .env and run file main.py or create docker-compose.yml

```yml
services:
  bot-app:
    build: .
    environment:
      DISCORD_TOKEN: your_discord_token_here
      CHANNEL_ID: your_channel_id_here
      ROLE_ID: your_role_id_here
      RCON_IP: your_rcon_ip_here
      RCON_PORT: your_rcon_port_here
      RCON_PASSWORD: your_rcon_password_here

```



## Commands

- `!@discord_user` Removes the mentioned Discord user from the whitelist. Only a user with the `ROLE_ID` or the mentioned user themselves can use this command.
- `!minecraft_username` Removes the Minecraft user from the whitelist. Only a user with the `ROLE_ID` or the user who added the Minecraft username can use this command.
- `minecraft_username` Adds a Minecraft user to the whitelist. Each Discord user can only add one Minecraft username to the whitelist. Users with the `ROLE_ID` can add multiple usernames.


## Authors

- [@ItsRaelx](https://github.com/ItsRaelx)


## License

- [ Apache License](http://www.apache.org/licenses/)