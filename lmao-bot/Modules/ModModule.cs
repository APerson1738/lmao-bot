﻿using Discord;
using Discord.Addons.Interactive;
using Discord.Commands;
using lmao_bot.Events;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Timers;

namespace lmao_bot.Modules
{
    public class ModModule : InteractiveBase
    {
        [Command("purge")]
        [Alias("clear", "clean", "prune", "obliterate")]
        [Summary("Remove a bunch of messages from your channel")]
        [RequireContext(ContextType.Guild, ErrorMessage = "This command can only be run in a server.")]
        [RequireBotDeveloper(Group = "Group")]
        [RequireUserPermission(GuildPermission.ManageMessages, Group = "Group")]
        [RequireBotPermission(GuildPermission.ManageMessages)]
        public async Task<RuntimeResult> Purge(int messageCount)
        {
            if (messageCount > 100) return CustomResult.FromError("You cannot purge more than 100 messages at a time");
            // Check if the amount provided by the user is positive.
            if (messageCount <= 0) return CustomResult.FromError("You cannot purge a negative number");
            var messages = await Context.Channel.GetMessagesAsync(messageCount).FlattenAsync();
            var filteredMessages = messages.Where(x => (DateTimeOffset.UtcNow - x.Timestamp).TotalDays <= 14);

            // Get the total amount of messages.
            var count = filteredMessages.Count();

            // Check if there are any messages to delete.
            if (count == 0) return CustomResult.FromError("Nothing to delete.");
            else
            {
                await (Context.Channel as ITextChannel).DeleteMessagesAsync(filteredMessages);
                await ReplyAndDeleteAsync($"Done. Removed {count} {(count > 1 ? "messages" : "message")}.");
                return CustomResult.FromSuccess();
            }
        }

        [Command("mute")]
        [Alias("silence", "shush")]
        [Summary("Mute a user in your guild")]
        [RequireContext(ContextType.Guild, ErrorMessage = "This command can only be run in a server.")]
        [RequireBotDeveloper(Group = "Group")]
        [RequireUserPermission(GuildPermission.ManageMessages, Group = "Group")]
        [RequireBotPermission(GuildPermission.ManageMessages)]
        public async Task<RuntimeResult> Mute(IGuildUser user, TimeSpan? duration)
        {
            try
            {
                if (user.Id == Context.Client.CurrentUser.Id) return CustomResult.FromError($"Silly {Context.User.Mention}, I can't mute myself!");
                if (!duration.HasValue) return CustomResult.FromError("You must include the duration");
                var channel = Context.Guild.GetChannel(Context.Channel.Id);
                await channel.AddPermissionOverwriteAsync(user, new OverwritePermissions(sendMessages: PermValue.Deny));
                string timeString = "";
                if (duration.Value.Hours != 0) timeString += $"{duration.Value.Hours} hours, ";
                if (duration.Value.Minutes != 0) timeString += $"{duration.Value.Minutes} minutes, ";
                if (duration.Value.Seconds != 0) timeString += $"{duration.Value.Seconds} seconds";

                _ = Task.Run(async () =>
                  {
                      Thread.Sleep((int)duration.Value.TotalMilliseconds);
                      await channel.RemovePermissionOverwriteAsync(user);
                      Embed e = new EmbedBuilder()
                      {
                          Title = "Notice",
                          Description = $"{ user.Mention } is no longer muted.",
                          Color = Color.Orange,
                          Footer = new EmbedFooterBuilder()
                          {
                              Text = $"Originally muted by {Context.User.Username}"
                          }
                      }.Build();
                      await ReplyAsync(embed: e);
                  });
                return CustomResult.FromSuccess($"{user.Mention} was muted in {Context.Channel.Name} by {Context.User.Mention} for {timeString}.");
            }
            catch (Exception ex)
            {
                await ReplyAsync(ex.ToString());
                await ReplyAsync(ex.StackTrace);
                throw;
            }
        }
    }
}
