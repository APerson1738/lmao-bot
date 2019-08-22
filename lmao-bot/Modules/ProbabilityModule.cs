﻿using Discord.Commands;
using System;
using System.Collections.Generic;
using System.Text;
using System.Threading.Tasks;

namespace lmao_bot.Modules
{
    public class ProbabilityModule : ModuleBase
    {
        [Command("coin")]
        [Alias("flip")]
        [Summary("Flip a coin!")]
        public async Task<RuntimeResult> CoinFlip(int coin = 1)
        {
            if (coin > 100) return CustomResult.FromError("You may only flip up to 100 coins at a time");
            else if (coin <= 0) coin = 1;

            if (coin == 1)
            {
                Random rnd = new Random();
                int result = rnd.Next(0, 1);
                int gender = rnd.Next(0, 1);
                string flip = "Heads! :man:";

                if (result == 0)
                {
                    flip = "Tails! :peach:";
                }
                else if (gender == 0)
                {
                    flip = "Heads! :woman";
                }
                await ReplyAsync(Context.User.Mention + " " + flip);
                return CustomResult.FromSuccess();
            }
            else
            {
                string coinMessage = Context.User.Mention + " You just flipped **" + coin + "** coins and got **";
                string coinEmoji = "";

                Random rnd = new Random();
                int heads = 0;
                int tails = 0;
                for (int i = 0; i < coin; i++)
                {
                    int result = rnd.Next(0, 2);
                    int gender = rnd.Next(0, 2);

                    if (result == 1)
                    {
                        coinMessage += "T";
                        coinEmoji += " :peach:";
                        tails++;
                    }
                    if (result == 0)
                    {
                        if (gender == 0)
                        {
                            coinMessage += "H";
                            coinEmoji += " :man:";
                        }
                        else if (gender == 1)
                        {
                            coinMessage += "H";
                            coinEmoji += ":woman:";
                        }
                        heads++;
                    }
                }
                coinMessage += "**!";
                string coin_results = "\n`Heads: " + heads + "`\n`Tails: " + tails + "`";
                await ReplyAsync(coinMessage + coinEmoji + coin_results);
                return CustomResult.FromSuccess();
            }
        }
    }
}
