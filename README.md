# Activitywatch_pavlok_check

This is just a small python script I wrote to get events from activitywatch, count the amount of time spent on a chosen filter and then depending on how long I have had an application with a matching title open give me a schock on my pavlok 3.  

It uses the remote function of the pavlok app which allows you to generate a url to share with friends. **When creating a url the name of the remote will be used in the url which can then be guessed by anybody. Please use a random name for your remotes to mittigate the risk** By allowing anonymous users, a simple web request can send you a schock. The code needed for an connection can be found in the url. Don't forget to add the code to the script if you wish to use it yourself. In the example below you can see where is is located in the url itself.
https://app.pavlok.com/unlocked/remotes/{pavlok_code}
When the servers of pavlok are unreachable you won't be able to schock yourself. The program will keep checking every 30 seconds. It is not uncommon for the server to be down. I have the script scheduled to only check between 00:00 and 17:00 which is when I want to be most productive. Having the script start up with my computer has helped me.

So yeah it really is just a convoluted anti-procrastination machine.
