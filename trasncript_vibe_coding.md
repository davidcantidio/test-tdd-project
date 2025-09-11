
Procurar no vídeo
Intro
0:00
I learned how to vibe code for you. So, here's the cliffnotes version to save you the hundreds, actually probably at
0:06
this point thousands of hours I have spent watching YouTube tutorials, taking courses, but honestly, mostly just like
0:13
trial and error as I'm developing my own applications through vibe coding. Vibe coding is seriously a gamecher and has
0:20
fundamentally changed the way that I code and develop apps. Which is why in this video I'm going to be focusing on
0:25
the fundamentals, the frameworks and the principles of good vibe coding. Then I'll also teach you how to apply these
0:31
principles of vibe coding with any tool. As per usual, it is not enough just to listen to me talk about stuff. So
0:36
throughout this video, there'll be little assessments. And if you can answer these questions, then congratulations. You would be educated
0:42
on vibe coding fundamentals. Now, without further ado, let's get going. A portion of this video is sponsored by
0:48
Brilliant. All right, here's the outline of today's video. First, I'm going to define vibe coding. Then we're going to
0:53
be talking about the principles of good vibe coding. I'll then show you some examples of vibe coding in action using
0:58
Replet Windsurf. Then finally, I'll end with some very practical tips to help you along your vibe coding journey and
1:04
to make sure that you don't end up as one of these people from X and Reddit who really up. I do not want that
1:10
for you. So, please pay attention until the end. Let's now define vibe coding. I'm sure many of you have heard the term vibe coding a lot of times by now. And
1:17
this is a term that was coined by Andre Kaparthy who among many of his achievements is one of the founding
1:22
members of OpenAI. On February 3rd, 2025, he made a post on X that says,
1:28
"There's a new kind of coding I call vibe coding where you fully give into the vibes. Embrace exponentials and
1:34
forget that the code even exists." It's possible because the LMS's, for example, Cursor Composer with Sonnet are getting
1:40
too good. You basically just tell the LM what it is that you want to build and it would just go ahead and build it for you and some people literally just speak to
1:46
it like talk to it. Also, I just talked to Composer with super whispers. I barely even touched the keyboard. For
1:51
example, you can just prompt it with something like create a simple React web app called Daily Vibes. Users can select
1:56
a mood from a list of emojis. Optionally, write a short note and submit it. Below, show a list of past
2:02
mood entries with the date and a note. And yeah, that's it. Give it to the LM and it generates the code for you. And voila, that's what you get. Seems very,
2:09
very simple. Crazy, right? You can see how it fundamentally changes the way that you code and and build things. But
2:16
with that being said though, it's not like black magic and vibe coding will magically just work for everything. There are still principles and order in
2:22
this chaos in how it is you ask it to build these things. So without further ado, let's actually cover these
2:29
principles. The best course that I found that covers the principles, the fundamentals of vibe coding is a course
Vibe coding fundamentals
2:35
called Vibe Coding 101 with Replet. It's a nice little free course that's created by Replet, which is a platform for vibe
2:41
coding apps in collaboration with deep learning AI. The course explains that there are five fundamental skills in
2:46
vibe coding, which are thinking, frameworks, checkpoints, debugging, and context. You need to thoroughly think
2:51
through exactly what it is that you want to build and then communicate that with the AI. What we mean by think thoroughly
2:57
is actually four different levels of thinking. Say, for example, you want to program a computer to play competitive chess. The first two levels of thinking
3:03
are probably really obvious and it's just like very intuitive to you. Logical thinking is just what is the game and in
3:08
this case the game is chess. The next level analytical thinking is asking the question how do I play this game? What
3:13
is the main objective the goal of the game? Now the third level is computational thinking. You need to figure out how to fit the logic of this
3:20
game into a complicated set of problems and configurations on the chessboard. You also need to think about how do you
3:25
enforce these rules. And finally at the top level of thinking is procedural thinking. This is when you ask the
3:31
question how do I excel in this game? Not only do you want to play this game, you want to play it well. So, you need
3:36
to think about what are some strategies that you can use. What are the boundaries that you can push so that
3:41
you're able to program your computer to be able to do well at the game. Then, of course, you need to translate this natural language that we described and
3:48
communicate that to the AI to build. Now, for whatever it is that you're trying to build, a game, a web app, whatever, you also need to go through
3:54
these four levels of thinking to truly properly define what it is that you want to build. Honestly, this is where most
3:59
vibe coders have the most opportunity for improvement. Because oftent times because you're using natural language
4:05
just to describe what you want to do, you don't really actually think through what it is that you want to build, what it is that you want your final product
4:11
to look like. And that's actually kind of unfair because if you don't even think through exactly what it is that you want, how do you expect the AI to be
4:18
able to figure out what it is that you want built? And actually, the best way to make sure that you go through each of these levels of thinking and communicate
Example PRD
4:25
it clearly to the AI is to create something called a PRD, which is a product requirements document. This is
4:30
an actual PRD that we defined with one of our clients. It is an AI powered personalized nutrition plan for
4:36
diabetes. Level one of thinking which is logical thinking defining what it is that we want to build. So this is as
4:41
part of the project overview. We wrote that the goal of this project is to develop an AI powered system that
4:46
creates personalized nutrition plans for individuals with diabetes. The system will take into account various health related factors such as medical
4:52
analyses, weight, dietary habits, calorie consumption and more. The next level of thinking, the analytical
4:57
thinking is encompassed by the skills section. So this is where you list out what it is that you need in order to
5:04
build the thing that you want to build. In this case, we wrote Python, healthcare data processing, open AIS API, image processing for visual plans,
5:11
and UI development. You can you can also go into more detail about this if you want if you're very if you're more particular about which specific packages
5:18
you want to use, which kind of front end, which kind of backend that you want to use, but this is good enough to start. For computational thinking, I
5:24
like to express this by having a key features section in the PRD. This is
5:30
where we can clearly define and have a plan based upon what we want to show up in the application. Here we have it
5:36
divided into milestone one and milestone 2. The first one is a generalized personalized nutrition plan engine that includes specific metrics like
5:42
individual health metrics and socioeconomic factors. The level two is where we want to give more contextual customization specifically considering
5:50
people's literacy and education levels and making the application adaptable um
5:55
and more accessible to different types of people for example people with lower literacy. Now for procedural thinking
6:00
the highest level of thinking thinking about how do we make this application the best that it can be this is
6:06
exemplified throughout the PRD just by adding as much detail as possible. For example, defining exactly which factors
6:14
like individual health metrics like medical analyses and dietary intake data and socioeconomic factors such as income
6:20
location and local food availability as well as what types of contextual customization. But the best way to think
6:26
about it is the more detail you can go into thinking about your target audience, who you want to be using your
6:31
application and that experience that they should get and all the factors that go into it to make it the best
6:37
experience possible. the clearer your vision is and the clearer the PRD is and the better results you will get from the
6:42
AI. Also, just by the way, you don't need to come up with this PRD all by yourself. Um, I'm actually going to put
6:47
like a prompt on screen right now. Feel free to take a screenshot of this. This prompt will work with you and ask you
6:52
the right questions for you to be able to come up with a well-defined PRD to build your app. I highly recommend that
6:58
you spend a significant amount of time at this section. It is always so much easier to have a clearer vision of what you want as opposed to build something,
7:05
figure out that it's not exactly what you want, and then try to fix it halfway. The next principle of vibe coding is to know your frameworks,
Frameworks
7:12
whatever it is that you want to build, chances are somebody has already built something like it or something very, very similar to what it is that you're
7:18
trying to accomplish. And since AI is trained on all the pre-existing solutions that are already available, if you're able to direct the AI towards the
7:26
correct framework for building what you want to build, you're going to have much better results than asking it to just
7:31
try its best to come up with something from scratch. And the easiest way to do this in vibe coding is just to list out
7:37
the frameworks or the packages that you want the AI to use to implement the solution that you want. You're kind of
7:42
just like pointing it in the right direction. For example, for your web app, you can specify that you wanted to use a React backend and a CSS and HTML
7:50
JavaScript front end and specifically maybe Tailwind CSS for the styling for this specific type of application. Or
7:56
say that you want to be creating animations, you can specifically say please use 3.js which is a very popular
8:02
package for creating animations. Okay, so the question you might be thinking right now is like Tina, but what if I
8:08
don't know what is the best way of implementing this thing? No problem. You can actually ask AI to help you figure
8:14
it out first. For example, if you want to implement a drag and drop UI, which is a very common thing to implement, you
8:19
could say, could you help me come up with some React frameworks to implement drag and drop into this application and then implement it. What is actually the
8:25
key thing here is to be open to learning about these different frameworks and how all of these components fit together.
8:31
With vibe coding, it's not necessary for you to exactly know how to implement each of these things yourself, but it's
8:37
still really important to have an understanding of the structure of what it is that you're trying to build. Like
8:42
if you're making a web application, at the very minimum, you should be aware of what a front end is, what a backend is,
8:48
how the front end and backend communicate with each other, and what are certain frameworks that are very popular or commonly used for the front
8:54
end and the back end. Think about it as building and developing and learning with the AI at the same time. This will
8:59
make you a much better vibe coder in the long run. The next principle of vibe coding is to always have checkpoints and
9:06
version control. Things will break. That is a fact. You do not want to end up like this guy, for example, who lost all
9:12
of his work because he did not know about version control. It is a cautionary tale. He posted on X, "Today
9:17
was the worst day ever. The project I had been working on for the last 2 weeks got corrupted and everything was lost.
9:23
Just like that, my SAS was gone. Two weeks of hard work completely ruined. But I mean he is trying to stay positive
9:29
here. He started from scratch. Blah blah blah. He's going to rebuild everything from cursor. So you know at least he's remaining positive. But anyways the
Using Github for version control
9:34
point being that please always have version control. There are some software like replet for example that has pretty decent version control that's already
9:41
built in. But for the majority of software and it's just like generally best practice is to learn how to use git
9:46
and github which I'm actually going to give you a crash course on right now. If you already know how to use git and
9:51
github consider this a quick little refresh. So first of all git is the version control software itself. While
9:57
GitHub is a website that allows you to store your code, your repositories on the cloud so that you're able to have
10:02
it, you know, saved somewhere else and also so that you can share it with other people. So, first you need to install git and you can do this by either
10:08
downloading it from the website or you can go through your terminal/comand line or honestly you can just ask your AI
10:14
code editor software whether that be like replic whatever and just directly say like please download git for me. Now
10:21
assuming that you want to start a new project from scratch and you're in that current folder the command that you want to use is get init which is initializing
10:28
git. Now let's say you start adding some things you might want to add a readme where you know you just start like vibe coding and now you have a bunch of files
10:34
that are there. And if you use this command get status it will show that you have a lot of files that are unttracked.
10:39
So in order to track these files you use the command git add. You can do get add like readme.md or whatever files that
10:46
you want to start tracking. Or you can just do get add with a dot. The dot means just track everything. But you're
10:52
not done with just adding these files and tracking these files. When you actually want to save a certain version of it, you use the command git commit.
10:58
This is where you would explicitly commit the changes that you made to the files. And you can also type a message that explains what you changed in the
11:05
codebase or otherwise known as the repository. For example, your first commit could be git commit-m with
11:11
initial commit as the comment. And that's it. Actually, if you just do this, you would be tracking your changes, saving your changes by
11:18
committing it. And you just keep on doing that. And if you ever want to look at the changes that you made, you can use a command called get log. And if you
11:24
want to roll back a commit, then it's git reset. Okay. So after you made a bunch of changes, did all your things, and maybe you want to share your code
11:30
now on GitHub. You can go to github.com, create a new repository, and initiate it. Copy the remote URL, then use the
11:36
command get remote at origin, and then the URL. This will link your local repo that's being saved on your computer to
11:42
GitHub. Then you might want to rename your branch, which is the current repository version that you're working with and call it main. So you can do git
11:50
branch- m main. Then finally, you can push everything from your local repository onto GitHub with the command
11:56
git push- origin main. There are obviously like a lot of other little nuances and commands and like things
12:02
like that um specifics that you can go into a lot more detail about, but just knowing what I explained to you that
12:08
entire workflow, that should be enough for you to have a good understanding of what version control is supposed to look
12:13
like and what the flow is supposed to look like. And even though I did cover the exact commands that you should be inputting using an AI code editor, you
12:19
actually don't need to know these exact commands. Like as long as you know what that structure is, you can just directly ask the AI using natural language. like
12:27
you can just say um use git to commit these changes, push it to GitHub on this branch, roll back the previous version,
12:33
merge everything together. I hope that makes sense. Overall, I hope you can also see that the key to vibe coding is
12:39
to understand these like highle structures, these highle components and the flows of things so that you're able
12:45
to direct the AI in the implementation. Implementation is where AI excels at.
Debugging your vibe code
12:50
The next important skill of vibe coding is debugging. Whatever it is that you're building is going to go wrong. It's just
12:55
a matter of when it's going to go wrong and how it's going to go wrong. Which is why debugging and fixing the thing is
13:00
just as important as the actual building itself. This is a skill that is drilled into engineers with many many years of
13:06
training. But for many vibe coders though, especially those who don't have an engineering or coding background, debugging might be something that they
13:13
don't actually have a lot of experience in. And it's very important to learn this skill. The best type of debugging
13:18
is very methodical and thorough. First, you need to identify where the problem is and what the problem is. then you
13:23
need to apply different solutions to try to fix the problem. Sounds super simple, right? But do not underestimate the art
13:29
of debugging. In the case of vibe coding, when you realize that something doesn't work, um I actually find that
13:34
the best way is to just point it out to the AI and then let the AI come up with the solutions to fix it itself. For
13:41
example, I recently did this live stream where I was building this application and then it kept on coming up with an
13:46
error. I basically just copy pasted the error message and went like there is an error and the AI responded with like oh
13:51
let me try to fix it. and then it comes up with like different solutions to try to fix the problem. And really all you have to do often times is just to accept
13:57
the changes and if it still doesn't work it might just go through like a lot of cycles of this. Just got to be patient and just you know keep pointing it out
14:03
letting it do its thing and often times it resolves itself but in the off chance that it doesn't resolve itself easily.
14:09
It is really really helpful to have a basic understanding of what you're building. Like for example, I kept on
14:14
getting the same error over and over again. But since I understand file structures and how the files are working with each other, I was able to point out
14:20
which file was probably causing the problem and which section was probably causing the problem and the AI was able
14:26
to go and fix it. Another example was when I got this overlapping UI component which I didn't like. I was like this
14:32
thing is overlapping. I sent it to the AI and then it like made some weird changes and the whole thing just disappeared. And then I was very patient
14:38
and was more specific about exactly what it is that I wanted. And looking at the code, I could tell that it was just statically trying to input like a
14:45
certain dimension so that depending on the orientation of the website, sometimes it would overlap and sometimes
14:51
it wouldn't. And then I just pointed out that I needed to be dynamic so that it's not overlapping at any point. And then fortunately, it was then able to fix it.
14:58
And finally, the last principle of vibe coding is to provide context. The
15:03
general rule of thumb is that the more context, as in the more information and detail that you can provide to your AI,
15:10
to your LM, the better the results are going to be. And context can come in a lot of different forms. It could be that
15:16
the original prompt or the PRD that you're inputting has a lot of details in it. You can even provide it with like
15:21
mockups of what exactly you want it to look like. Or you can be providing it with examples or extra data that can
15:26
help it build the application. Details about your app, your environment, your preferences, as well as errors. Instead
15:32
of just saying this thing doesn't work, you can actually copy paste the full error message and a screenshot of what
15:38
exactly doesn't work and provide that to the AI. Okay, so here's a little pneummonic that can help you potentially
15:43
remember these principles of vibe coding better. The friendly cat dances constantly thinking frameworks,
15:49
checkpoints, debugging, and context, which immediately comes in handy for you now because here's also your little
Quiz 1
15:55
assessment, which I'm going to put on screen right now. Please answer these questions and put them in the comments
16:00
to make sure that you're following along with the things I am talking about. I'm now going to show you some examples of
Replit vibe coding demo
16:06
vibe coding starting with Replet. Replet is a platform where you can use AI to vibe code different applications and
16:12
deploy them really really quickly all on the cloud. It is super beginner friendly. All you have to do is log on to Replet and they have some free
16:19
credits that you can get started with. Let's start off with the PRD for a very simple app that displays SEO metatags
16:24
for any website that is inputed. Okay, so to get started, the first thing I'm going to do is actually use chatgbt to
16:31
help me really think about what I want this application to look like and generate a PRD for it. And I'm going to
16:38
use this prompt over here, which is a variation of the prompt that I showed you guys earlier. And I'll also link an
16:45
example PRD for chatt. So it just says, help me to make a PRD for an MVP app.
16:50
I'm looking to vibe code. So, an interactive app that displays the SEO metatags for any website in an interactive visual way to check that
16:56
they're properly implemented. The app should fetch the HTML for a site, then provide feedback and SEO tags in accordance with best practices for SEO
17:03
optimization. The app should give Google and social media previews. And then thinking through these questions, what
17:08
is this app? How do I use the app? What are the patterns behind the app? And how do I make the app the most useful for the target audience? And including a PRD
17:15
example here. And it helps us generate this. So, SEO tag, visual inspector, MVP, PRD, project overview, and it shows
17:23
all of the key features that are here. So, input URL field, HTML fetching and
17:28
parsing, SEO tag extraction, and visual feedback previews. And there's also a
17:33
nice to have section. All of this looks pretty good. I do want to have a key feature of actually displaying the total
17:40
score out of 100. I also do want to get rid of these nice to have haves over here cuz it's always best to start off with the very very key features and then
17:47
add on to that. So I'm going to ask it to refine it with for key features.
17:53
Could you include a total score out of 100? Also remove nice to haves. Great.
18:01
So visual feedback is over here. Awesome. So this looks pretty good to
18:06
me. So, I'm going to write is could you make this into a prompt uh to build an
18:13
app using replet? So, that's what we're going to use. Great. Wonderful. And on top of this, I'm going to say generate a
18:21
image mockup or inspo. I'm going to download this. Here is a replet. And
18:26
what I'm going to do is just copy paste the prompt from chatbt and also link the
18:33
inspo and click start building. All right, it's going to be called SEO Tag
18:38
Scout and it's asking me if I want these like additional things that are here and
18:43
I'm just going to say no because we can add these additional features later. So, we can approve and get started. As it's
18:49
generating, you can see that it's literally designing the visuals and it's also populating the files over here as well. So, for Replet, it already does
18:57
have pretty good um version control. You can roll back pretty easily here. Although for best practices, you still
19:03
really do want to be using Git at some point. While it's finishing up building everything over here, what I really recommend that you do is you can go over
19:10
here and actually add an assistant and use the assistant and ask, could you
19:16
explain to me the file structure in this project? You don't have to do this, but
19:21
it's one of those things where if you're learning about the frameworks that are being used while you're vibe coding, this is going to significantly improve
19:28
your skills as a vibe coder because you're going to be able to understand what's actually happening and how the files are going to be interacting with each other. We can see over here on the
19:34
client side under client, you have the main React application code in the source. So, client source and you can
19:42
see where the UI components are as well. And on the server side, it tells you where the main service entry points are
19:47
like index.ts. And here's the code for that. And then roots and things like that as well. Just understanding the
19:53
files over here and how they're interacting with each other to produce this completed app is already going to give you a huge leg up. And if you
19:59
really want to dig into like some of the actual code, you can always rightclick over here and then you can say like
20:05
explain with assistant for example. This is very very optional, but it is a really really great way for you to learn
20:11
um what the code is actually doing if you're interested. All right, it looks like our app is now finished. Let's actually test this out. So, let's try
20:19
ww.lonely octopus.com. Check. Uhoh, that didn't
20:24
work. So, what I'm going to do is there is an error like a true vibe
20:32
coder. We're going to hope that it fixes itself. Okay, let's try testing it out again. Lonely
20:38
octopus.com. And cool, it seems to be showing something. the title, shorter than recommended, meta description, blah
20:45
blah blah, all of these things. And we can see that here's the Google preview, here's the social media preview, Twitter
20:51
card previews, and raw data tags. Okay, so I just want to make sure that the like number actually changes depending
20:57
on the website. So let's try something else like the website called the useless website.com. Okay, so it's also still
21:04
showing 86. What about this other website? Okay. All right. So the number is changing depending on what it is.
21:12
It's like this is not visually appealing. Make it colorful. Yeah, make
21:19
it colorful. I also don't like how the raw data tags are here, but it's not specifically specifying like what the
21:26
title is sort of the recommend like what is the actual title. Like I want that to be showcased and I'm going to do that in the next round of edits here. Another
21:32
key thing to remember is that it's best to when you're pointing something out, like something that you want to be changed, doing it one at a time as
21:39
opposed to like a laundry list of things that you want to change cuz that could potentially confuse the AI. Oh, cool. I guess it did that already without me
21:45
saying anything. Oh, and it's like showing little icons. So, that's nice. Okay, let's try this again. lonely
21:52
octopus.com. Okay, I like that. This is much much better. Another thing that you can do over here is that you can
21:58
actually click here and then there is a dev URL that you can directly look at
22:03
from other devices as well. So all you have to do is scan the QR code. So you can actually see what it's like on other
22:09
devices too. So if I were to type lonely octopus.com, you can see what that
22:14
experience looks like on mobile as well. So this is a example of what it would
22:19
look like to be web coding using Replet. And once you're done, you can take this and deploy it when you want to. But if
22:27
you do want to create something that is more complex and that's also more scalable, you will at some point want to migrate to a AI code editor, something
22:34
like Windsor for cursor. So I'm actually just going to show you what that is like um using Windinserve for example. First
Comparing vibe coding tools
22:40
of all, regardless of which of these tools that you're using, the principles that we just talked about for vibe coding, like the skill set itself is
22:46
pretty much the same. So don't worry about that. It's more the fact that after you get through the beginner stages, most people will want to switch
22:51
over to AI coding editor like cursor and windsurf because it's more robust, has more functionalities, and also allows
22:57
for greater scalability. Of course, with these types of things, there's always a trade-off. Like with Replet, it is a lot faster, really easy to use. Everything
23:04
is based on the cloud. So, you don't really have to deal with setting up your environment and the deployment process. While for cursor and windsurf, there are
23:10
a lot more functionalities that are available. These code editors are built for like full scale development. So
23:15
you're pretty much able to do any type of development and be able to tweak things and fine-tune things to the exact
23:21
way that you want it to look. Of course, the downside is that there is a higher learning curve. You need to learn how to set up your environments properly, how
23:27
to debug issues with your environment. A lot of issues come because of not setting up your environment correctly.
23:32
You also need to learn how to deploy things, how to monitor things over time. So this is the wind surf environment and
Windsurf vibe coding demo
23:37
over here is cascade where you can type in what you want the app to build. In
23:42
this case we're using cloud 3.7 sonnet as the model. So I'm actually going to put in the exact same prompt and then
23:49
also the image as well on winds. This is going to be a local development environment. So it's going to start off
23:55
by setting up a bunch of things locally. You can see that the files are populating themselves over here as well.
24:03
All right. So this is running a terminal command and we can accept this. It's you can disable and the asking and you can
24:10
just let it auto run but I have trust issues cuz it's on my local environment instead of like rep play where it's in its like own isolated thing on the web.
24:16
So I do like want to make sure that I am accepting things and not doing random
24:23
things to my local environment. So I'm just going to click accept to all of these. You can see that it also takes a little bit longer cuz it's setting up
24:29
all these environments and selling all these packages and stuff. Um, all things that don't need to be done if you're
24:34
using Replet. Okay, cool. It looks like it has something done. It says, "Feel free to try it on the browser preview
24:40
I've opened for you." Open the browser preview. I don't see the browser
24:48
preview. Could you open it for me? Okay. Open preview.
24:54
Cool. We see that it has some of these very similar elements here. www.lonely
25:01
Lonely octopus.com for example check. Oops.
25:06
Need to adding an https. Okay, this actually looks way better than replet's first version. I
25:13
got to say it actually looks really really similar to the inspo that we provided. It like here's the inspo that
25:19
we provided and here's the actual thing. It looks really similar, right? Looks pretty good. So SEO tag analysis. Yeah,
25:26
this looks pretty good to me. Let's try something else.
25:34
maze.toys/mazes/min/aily. It's just like a random website. Okay. SEO tag is 25. So the numbers are actually different um
25:41
between Replet and Windfs. So that's interesting. Something I probably want to dig into asking like how it's
25:47
calculating these SEO tags. But overall it looks like it's working pretty well. And I quite like this. So I'm going to
25:54
ask it to change though. To improve on this a little bit, I'm going to say edit
25:59
a screenshot here and be like make it so that you don't need to type
26:04
https before the URL. Also, copy paste is not enabled. Let's open a preview
26:12
again. So, try this again. www.lonely octopus.com. We also do need to center
26:18
this later. And it still doesn't work. So, I'm just going to write still doesn't work. Let's try again. lonely
26:26
octopus.com. Okay, cool. So, that works now. Um, obviously there's like other things that we want to fiddle around
26:31
with a little bit like things that are not centered. Might want to change these colors a little bit, but I hope this gives you a good idea for how it is that
26:38
you can start building using windsurf as the experience. And so, in this case, you also definitely do want to start using git and github as well. So what
26:45
you can do is be like initiate git for version control and just type that in.
26:51
Accepting everything here and then git is going to be initialized. Everything here turned green which means that it's
26:57
unttracked. It asked do you want to get add everything? We can accept get add everything and it's asking us if we want
27:03
to commit as well as our initial commit. So we can accept we can get commit to. So great now everything is being tracked
27:09
as version control. And when you're ready, you can also get push and you can actually see everything now on GitHub.
27:15
But regardless of what you use, remember the principles that we went through for vibe coding. Do keep those in mind and
27:20
apply them regardless of what kind of tools that you're using. I'm going to put on screen now a little quiz. So please type the answers in the comment
Tips & best practices
27:26
section. And now let's go on to our final section where I'm going to give you some more tips and tricks and
27:31
frameworks and mindsets that will help you along your Vibe coding journey. The first one is very much a mindset. If
27:37
you're already an engineer, you know, you probably already think this way. But if you're someone who maybe doesn't come from more of a technical background,
27:43
always think about starting small and working your way up. In other words, whatever it is that you're creating, always think about it as the minimal
27:50
viable product, which is what are the minimum amount of features that you can put into your application for it to
27:55
function. After you get the thing to actually work, then you can iterate and put on like additional features and functionalities on top of that. This is
28:01
the correct vibe coding mindset as opposed to you coming up with like the most lavish, you know, thing with all
28:08
the details that you can possibly think of and like a million different features. No, no, no, no. I can already think of all the errors and issues that
28:14
you're going to get from that and then just you like ripping out your hair because you can't figure out what's going wrong. Always start with the
28:20
minimal viable product and then iterate on top of it. Get the thing to work first. Next up is a framework that's also from the vibe coding 101 course,
28:26
which I think is really, really helpful. It shows that when you're developing or building an app, when you're vibe coding, there's really only two modes
28:32
that you're in. You're either implementing a new feature or you're debugging errors. When you're implementing a new feature, what you
28:38
want to remember is to provide context relevant to the new features. Mention frameworks, provide documentations with explicit details, etc., and then making
28:45
incremental changes and doing the checkpoints and and version control, etc. And when you're in debugging errors
28:50
mode, what you want to keep in mind is firstly figuring out how things work. Do you have a good understanding of the structure of your project itself? if you
28:57
don't, you know, ask AI and and actually figure that out because it's going to be very helpful to figure out what is actually going wrong in your
29:03
application. And when you figure out what's wrong, think about how to get that information to the LM to get unstuck. And this is where the final
29:09
principle, context, is helpful. Just try to provide as much context and information as possible to guide your
29:15
LLM to fix to fix the problem. Give it like screenshots of what's wrong. Give it the error message, point it towards
29:21
the right file to be looking into. I really love this framework. So take a screenshot or something and whenever
29:26
you're getting frustrated or not know what you're supposed to do, just try to remember which mode that you're in and
29:31
what you should be doing in which mode. Final tip that is a little bit more advanced and these are writing rules or
29:37
documentation. This is kind of like a system prompt that you're giving to your coding agent. And this is where you can
29:42
list out like certain things that you wanted to do or to not do. For example, some of the best practices that you probably want to put in your rules
29:48
include limit code changes to the minimum when implementing a new feature or fixing something. This is because AI
29:54
sometimes has this tendency of like changing a lot of different files um unnecessarily to fix like a very small
30:01
thing and then it could potentially break other issues. Rate limit all API endpoints. This is just to make sure that you're not like calling an API and
30:09
incurring like multiple times and incurring a lot of cost. Enable capture on all authors and signup pages. So for
30:14
security reasons and yeah there are a lot of other rules that you can put into this file. You can also find online like
30:19
people have written these rules that are specific to like certain types of apps or certain languages that you're using
30:25
as well that you can put into your rule file as well. And you can take this rule file and give it to replet where cursor
30:30
ruins surf too. Especially if you're someone who doesn't come from an engineering background or like a development background, I really
30:35
recommend that you actually look into the rules that are specific for ensuring
30:40
like safety and security in your apps. Like putting it in your at least like learn things about like API keys and why
30:46
it is that you shouldn't be exposing your API keys. And while you're learning these, also put your rules into your rules file so you're reminding your AI
30:53
to be abiding by best security practices as well so you don't get hacked. All right, there is honestly like a lot more
30:59
that I can go into detail about. Like for example, like having styling documents that you can reference, how you should be refactoring your code,
31:06
using something like MCP servers. if you're building something like AI agents and you want to give your AI agents like
31:11
more tools and functionalities. There's just like a lot which I don't have time to cover in this video right now. But
31:17
please do let me know in the comments if you want me to make a follow-up video where I will go more in detail about
31:22
exactly how it is that you should be vi coding and giving you more specific advanced examples for AI code editors
31:28
like windsurf or cursor as well. But for now we have come to the end of this video. I really hope this vibe coding
31:33
fundamentals video is helpful for you to get started um doing it correctly like vibe coding with best practices in mind.
Quiz 3
31:41
And as promised, here is the final little assessment which do answer these questions and put in the comments to
31:46
make sure that you retain the information that I just covered. If you're watching this video and interested in vibe coding, chances are
31:52
you're probably also interested in learning STEM subjects. So, if you are interested in learning STEM subjects, I
31:57
highly recommend that you check out Brilliant, the sponsor of this portion of the video. Brilliant is a STEM learning platform that helps you get
32:03
smarter every day with thousands of interactive lessons in math, science, programming, data analysis, and AI. What
32:09
I love about Brilliant is that it helps you build critical thinking skills and deep understanding of subjects instead
32:14
of just memorizing things. Brilliant incorporates little quizzes, analogies, and just little dopamine hits that
32:20
really help a lot when you're getting bored or discouraged. It's shown to be six times more effective than just watching video content. They also have a
32:26
great mobile app so you can actually dig into a quick little session and learn something new when you have a couple minutes instead of just mindless
32:33
scrolling. Brilliance programming courses are some of my favorite courses. They help you build a foundation of coding and teaches you how to think like
32:39
an engineer, a skill that is still crucial in the age of AI and the age of vibe coding. Speaking of which, they
32:44
also have great AI courses, too, that can help you gain a deep understanding of how AI models work and their
32:49
applications. Brilliant courses are super high quality and taught by award-winning teams of teachers,
32:54
researchers, and professionals from Stanford, MIT, Caltech, Microsoft, Google, and more. To try everything that
33:00
Brilliant has to offer for free, you can visit brilliant.org/tina or just scan the QR
33:06
code on screen. Or you can also just click the link in the description. If you use my link, you also get a 20% off
33:11
the annual subscription. Thank you so much, Brilliant, for sponsoring this portion of the video. Now, back to the video. Thank you so much for watching
33:17
this video and happy vibe coding. I'll see you guys in the next video. We're live stream.

