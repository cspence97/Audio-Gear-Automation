# Audio-Gear-Automation
Automates finding the best deals on pro audio gear

## Purpose
I made this bot in order to both further my understanding of automation and also to potentially find some great bargains on new gear for my studio.  DO NOT use this without getting expressly written permission from Reverb first

### Function
The bot searches through listings of pro audio on reverb.com and compares active listings to last 10 transactions.  Returns three lists: one for gear discounted more than 25%, one for gear discounted 11-25%, and one for damaged or broken gear discounted more than 40%

If you want to use this to find good deals on other equipment, like effects and pedals or acoustic guitars, just replace the link in driver.get("https://reverb.com/price-guide/pro-audio") with the link to whatever other reverb price guide is desired.  
