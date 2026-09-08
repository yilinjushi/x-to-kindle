---
url: "https://x.com/LexnLin/status/2050179260892029179"
title: "How To Turn An Image Into A Website (EXAMPLE)"
author: "Leon Lin @LexnLin"
source: "x_bookmark"
date: 2026-09-08
chars: 3782
images: 12
---

# How To Turn An Image Into A Website (EXAMPLE)

You may have read this tutorial and still asked how do I turn gpt-images-2.0 generated images into code using for example codex.

This tutorial should hopefully clarify everything with an example :)

Leon Lin
@LexnLin
·
Apr 27
 Article
Building Better Frontends with an Image-to-Code approach
Most AI-generated websites still look average or sloppy.
Not because the models are useless, but because the workflow is usually wrong. People ask a coding agent to “make it modern,” “make it clean,”...
16
43
341
78K

## Generate images of the website you like

Step one is to generate images for your website on chatgpt.com using 
https://github.com/Leonxlnx/taste-skill/blob/main/skills/imagegen-frontend-web/SKILL.md

Copy the content of the file and drop it into the prompt or add the Markdown file.

![Article image](/assets/2026-09-08-how-to-turn-an-image-into-a-website-(example)-2b8429c190/01.jpg)

In this example I used this prompt:

Based on this skill above, generate images for a website for an AI agency. The design should include eight sections, with one image per section, eight distinct images in total. The website should feel polished and clean and rather minimalist with less info, but with striking image effects/visuals and creative layouts. Use orange as the main color. All images should be horizontal

TIPS:

- Please run your prompt multiple times in different chats to get more results to choose from

- Use thinking mode for better quality

- Generate one image per website section

- images 2.0 can generate up to 10images at once

## Optional: refine/iterate till you get the perfect result

Just prompt and refine in chatgpt till you get a really nice result.

Use this to edit one image at a time.

![Article image](/assets/2026-09-08-how-to-turn-an-image-into-a-website-(example)-2b8429c190/02.jpg)

Or change the style of all images.

![Article image](/assets/2026-09-08-how-to-turn-an-image-into-a-website-(example)-2b8429c190/03.jpg)

If you're done, download all images.

## Extract all images

Now you need to extract all assets from your images. So this means for example these:

![Article image](/assets/2026-09-08-how-to-turn-an-image-into-a-website-(example)-2b8429c190/04.jpg)

![Article image](/assets/2026-09-08-how-to-turn-an-image-into-a-website-(example)-2b8429c190/05.jpg)

This is how I extract these images:

![Article image](/assets/2026-09-08-how-to-turn-an-image-into-a-website-(example)-2b8429c190/06.jpg)

Prompt:

extract the images on the right, generate them total should be 7 extracted generated images, please dont change them, they should look exactly the same

![Article image](/assets/2026-09-08-how-to-turn-an-image-into-a-website-(example)-2b8429c190/07.jpg)

Prompt:

in this image there are 4 images used. extract them and generate all 4. so generate 4 different images in total

## Remove background of your assets

Sadly chatgpt no longer has the feature of generating transparent images anymore (hope it will be there again soon :))

I personally use https://express.adobe.com/home/tools/remove-background (free)

![Article image](/assets/2026-09-08-how-to-turn-an-image-into-a-website-(example)-2b8429c190/08.jpg)

## Turn it into a website

I'm using Codex for building this website.

Work on one section everytime. 
Start by adding your first section and prompting something like this:

lets build a website. 
i will provide the images and you just clone the rest of the website. so do NOT generate or build the asset in this image. focus on the components and details. 
here is the hero section. copy it. after that give me the dir of the folder where i need to put my images in  use react + nextjs 
start local dev server afterwards

![Article image](/assets/2026-09-08-how-to-turn-an-image-into-a-website-(example)-2b8429c190/09.png)

Afterwards codex will cook and tell you something this:

![Article image](/assets/2026-09-08-how-to-turn-an-image-into-a-website-(example)-2b8429c190/10.png)

Put your asset image that you extracted into that folder. 
(Either refresh the site or tell codex that you've added it)

And there you go

The result

![Article image](/assets/2026-09-08-how-to-turn-an-image-into-a-website-(example)-2b8429c190/11.jpg)

Original

![Article image](/assets/2026-09-08-how-to-turn-an-image-into-a-website-(example)-2b8429c190/12.jpg)

These were 2 prompts. You can refine it of course by fixing sizes and positioning of components.

Do the same for all the other sections. If you encounter alignment issues or overlapping:
Screenshot it, give it to codex, let it fix it

You need to be patient. Nothing crazy comes after one prompt.

“Good things come to those who wait.”

## Next steps

- Add scroll animations

- Add hover animations

- Focus on details and responsiveness

You can add these by just prompting Codex to add them:

Add animations when scrolling into a new section. Should feel smooth and clean

## My result

The media could not be played.
Reload

So everything you actually need is ChatGPT images 2.0 and Codex.

Github code: https://github.com/Leonxlnx/tutorialnexora

If you have questions, reply or dm me :)

Happy codexmaxxing!
