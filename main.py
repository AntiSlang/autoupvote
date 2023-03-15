import datetime
import os
import random
import time
import pyttsx3
import googletrans
import praw
from moviepy.editor import *
from PIL import Image, ImageFont, ImageDraw


def get_wrapped_text(text: str, original_font: ImageFont.FreeTypeFont, line_length: int):
    lines = ['']
    for word in text.split():
        line = f'{lines[-1]} {word}'.strip()
        if original_font.getlength(line) <= line_length:
            lines[-1] = line
        else:
            lines.append(word)
    return '\n'.join(lines)


def upvote():
    reddit = praw.Reddit(username="",
                         password="",
                         client_id="",
                         client_secret="",
                         user_agent='')

    subreddit_name = "askreddit"
    max_font_size = 175
    comment_count = 10
    subreddit = reddit.subreddit(subreddit_name)
    r_post = random.randint(0, 9)
    trans = googletrans.Translator()
    post_dict = {}
    for post_number, post in enumerate(subreddit.top(time_filter='day', limit=10)):
        if r_post == post_number:
            num_comments = f'{round((post.num_comments / 1000), 1)}k' if post.num_comments >= 1000 else post.num_comments
            score = f'{round((post.score / 1000), 1)}k' if post.score >= 1000 else post.score
            post_title = trans.translate(post.title, dest='ru', src='en').text
            print(post_title, post.title)
            post_title = post_title[0].upper() + post_title[1:]
            post_dict[post_title] = {}
            created_hours = str((datetime.datetime.utcnow() - datetime.datetime.fromtimestamp(post.created_utc)).seconds // 3600) + ' '
            created_hours += 'час' if created_hours[-1] == 1 else ('часа' if created_hours[-1] in list(map(str, range(2, 5))) else 'часов')
            try:
                post_author = post.author.name
            except Exception as e:
                post_author = 'anonymous'
            post_dict[post_title]['user'] = f'Опубликовано u/{post_author} · {created_hours} назад'
            post_dict[post_title]['num_comments'] = num_comments
            post_dict[post_title]['score'] = score
            post_dict[post_title]['comments'] = []

            img_p = Image.new('RGB', (1920, 1080), (30, 30, 30))
            drawing_p = ImageDraw.Draw(img_p)
            big_font_p = ImageFont.truetype("font.ttf", 1)
            middle_font_p = ImageFont.truetype("font.ttf", 45)
            fontsize_p = 1
            post_title_p = get_wrapped_text(' '.join([i if len(i) < 11 else i[:(len(i) // 2)] + '- ' + i[(len(i) // 2):] for i in post_title.split()]), big_font_p, line_length=900)
            while drawing_p.textbbox((0, 0), post_title_p, font=ImageFont.truetype("font.ttf", fontsize_p + 1))[3] < 800:
                fontsize_p += 1
                big_font_p = ImageFont.truetype("font.ttf", fontsize_p)
                post_title_p = get_wrapped_text(post_title_p, big_font_p, line_length=900)
                if fontsize_p == max_font_size:
                    break
            logo_p = Image.open('./images/askreddit.png').convert('RGBA').resize((int(693 * 1.3), int(693 * 1.3)))
            img_p.paste(logo_p, (900, (1080 - int(693 * 1.3)) // 2), logo_p)
            drawing_p.text(xy=(75, 120), text=post_title_p, fill="#ffffff", font=big_font_p)
            drawing_p.text(xy=(80, 50), text=f'r/AskReddit · {created_hours} назад · ▲ {num_comments} ▼', fill="#e7e7e7", font=middle_font_p)
            img_p.save('./images/preview.png')

            url = "https://www.reddit.com" + post.permalink
            submission = reddit.submission(url=url)
            submission.comments.replace_more(limit=0)
            submission.comment_limit = 3
            arr = []
            local_comment_count = 0
            for comment_number, comment in enumerate(submission.comments[:(comment_count + 20)]):
                tr_text = trans.translate(comment.body, dest='ru', src='en').text
                if len(tr_text) in range(13, 1100):
                    local_comment_count += 1
                    comment_body = comment.body
                    r_reply_count = random.randint(1 if len(comment_body) <= 50 else 0, 2)
                    try:
                        post_author_x = comment.author.name
                    except Exception as e:
                        post_author_x = 'anonymous'
                    score = f'{round((comment.score / 1000), 1)}k' if comment.score >= 1000 else comment.score
                    created_hours = str((datetime.datetime.utcnow() - datetime.datetime.fromtimestamp(comment.created_utc)).seconds // 3600) + ' '
                    created_hours += 'час' if created_hours[-1] == 1 else ('часа' if created_hours[-1] in list(map(str, range(2, 5))) else 'часов')
                    miniarr = [tr_text + f'u/{post_author_x} · {created_hours} назад · ▲ {score} ▼']
                    if r_reply_count != 0:
                        local_reply_count = 0
                        for reply_number, reply in enumerate(comment.replies[:(r_reply_count + 20)]):
                            rp_text = trans.translate(reply.body, dest='ru', src='en').text
                            if len(rp_text) in range(13, 1000):
                                local_reply_count += 1
                                try:
                                    post_author_x = reply.author.name
                                except Exception as e:
                                    post_author_x = 'anonymous'
                                score = f'{round((reply.score / 1000), 1)}k' if reply.score >= 1000 else reply.score
                                created_hours = str((datetime.datetime.utcnow() - datetime.datetime.fromtimestamp(reply.created_utc)).seconds // 3600) + ' '
                                created_hours += 'час' if created_hours[-1] == 1 else ('часа' if created_hours[-1] in list(map(str, range(2, 5))) else 'часов')
                                miniarr.append(rp_text + f'u/{post_author_x} · {created_hours} назад · ▲ {score} ▼')
                            if local_reply_count >= r_reply_count:
                                break
                    arr.append(miniarr)
                if local_comment_count >= comment_count:
                    break
            post_dict[post_title]['comments'] = arr
    tts = pyttsx3.init()
    tts.setProperty('voice', 'ru')
    tts.save_to_file(list(post_dict.keys())[0], './audios/start.mp3')
    tts.runAndWait()

    img = Image.new('RGB', (1920, 1080), (30, 30, 30))
    drawing = ImageDraw.Draw(img)
    big_font = ImageFont.truetype("font.ttf", 60)
    middle_font = ImageFont.truetype("font.ttf", 50)
    font = ImageFont.truetype("font.ttf", 40)
    post_upvote = f'▲\n{list(post_dict[list(post_dict.keys())[0]].values())[2]}\n▼'
    post_title = get_wrapped_text(list(post_dict.keys())[0], big_font, line_length=1500)
    _, _, w, h = drawing.textbbox((0, 0), post_title, font=big_font)
    _, _, wu, hu = drawing.textbbox((0, 0), post_upvote, font=big_font)
    drawing.text(xy=(300, (1080 - h) / 2), text=post_title, fill="#ffffff", font=big_font)
    drawing.text(xy=(300, ((1080 - h) / 2 + (h / 2)) - h * (1.3 if h < 100 else (0.8 if h > 150 else 0.95))), text=list(post_dict[list(post_dict.keys())[0]].values())[0], fill="#e7e7e7", font=font)
    drawing.text(xy=(300, ((1080 - h) / 2 + (h / 2)) + h * (0.85 if h < 100 else 0.65)), text=f'{list(post_dict[list(post_dict.keys())[0]].values())[1]} комментариев', fill="#e7e7e7", font=font)
    drawing.text(xy=(150, (1080 - hu) / 2), text=post_upvote, fill="#e7e7e7", font=middle_font, align='center')
    img.save('./images/start.png')

    numb = 0
    responces = []
    for number, com in enumerate(list(post_dict[list(post_dict.keys())[0]].values())[-1]):
        img = Image.new('RGB', (1920, 1080), (30, 30, 30))
        drawing = ImageDraw.Draw(img)
        big_font = ImageFont.truetype("font.ttf", 1)
        middle_font = ImageFont.truetype("font.ttf", 70)
        fontsize = 1
        ii = com[0].split('u/')[0]
        ii = get_wrapped_text(ii, big_font, line_length=1700)
        ij = com[0].split('u/')[1]
        while drawing.textbbox((0, 0), ii, font=ImageFont.truetype("font.ttf", fontsize + 1))[3] < 700:
            fontsize += 1
            big_font = ImageFont.truetype("font.ttf", fontsize)
            ii = get_wrapped_text(ii, big_font, line_length=1700)
            if fontsize == max_font_size:
                break
        drawing.text(xy=(100, 225), text=ii, fill="#ffffff", font=big_font)
        drawing.text(xy=(100, 100), text=ij, fill="#e7e7e7", font=middle_font)
        img.save(f'./images/image{numb}.png')
        tts.save_to_file(com[0].split('u/')[0].replace('\n', ' ').replace('*', ''), f'./audios/audio{numb}.mp3')
        tts.runAndWait()
        numb += 1
        if len(com) >= 2:
            for i in com[1:]:
                img = Image.new('RGB', (1920, 1080), (30, 30, 30))
                drawing = ImageDraw.Draw(img)
                big_font = ImageFont.truetype("font.ttf", 1)
                middle_font = ImageFont.truetype("font.ttf", 70)
                fontsize = 1
                ii = i.split('u/')[0]
                ii = get_wrapped_text(ii, big_font, line_length=1600)
                ij = i.split('u/')[1]
                while drawing.textbbox((0, 0), ii, font=ImageFont.truetype("font.ttf", fontsize + 1))[3] < 700:
                    fontsize += 1
                    big_font = ImageFont.truetype("font.ttf", fontsize)
                    ii = get_wrapped_text(ii, big_font, line_length=1600)
                    if fontsize == max_font_size:
                        break
                drawing.rounded_rectangle((100, 100, 110, 980), 3, fill="#8c8c8c")
                drawing.text(xy=(200, 225), text=ii, fill="#ffffff", font=big_font)
                drawing.text(xy=(200, 100), text=ij, fill="#e7e7e7", font=middle_font)
                img.save(f'./images/image{numb}.png')
                tts.save_to_file(ii.replace('\n', ' ').replace('*', ''), f'./audios/audio{numb}.mp3')
                tts.runAndWait()
                responces.append(numb)
                numb += 1

    EFFECT_DURATION = 0.4
    audio_clip = AudioFileClip(f'./audios/start.mp3', fps=44100).fx(afx.volumex, 1.5)
    audio_clip_transition = AudioFileClip(f'./audios/transition.mp3', fps=44100).fx(afx.volumex, 0.6)
    audio_clip = concatenate_audioclips([audio_clip, audio_clip_transition])
    video_clip = ImageClip(f'./images/start.png')
    video_clip = video_clip.set_audio(audio_clip)
    video_clip = video_clip.set_duration(audio_clip.duration)
    clips = [video_clip]
    durations = [audio_clip.duration]
    time.sleep(15)
    for i in range(numb):
        audio_clip = AudioFileClip(f'./audios/audio{i}.mp3', fps=44100).fx(afx.volumex, 1.5)
        audio_clip_transition = AudioFileClip(f'./audios/transition.mp3', fps=44100).fx(afx.volumex, 0.6)
        audio_clip = concatenate_audioclips([audio_clip, audio_clip_transition])
        video_clip = ImageClip(f'./images/image{i}.png')
        video_clip = video_clip.set_audio(audio_clip)
        video_clip = video_clip.set_duration(audio_clip.duration)
        durations.append(audio_clip.duration)
        clips.append(video_clip)

    img = Image.new('RGB', (1920, 1080), (30, 30, 30))
    drawing = ImageDraw.Draw(img)
    big_font = ImageFont.truetype("font.ttf", 112)
    post_title = 'Спасибо за просмотр!'
    _, _, w, h = drawing.textbbox((0, 0), post_title, font=big_font)
    drawing.text(xy=(300, (1080 - h) / 2), text='Спасибо за просмотр!', fill="#ffffff", font=big_font, align='center')
    img.save('./images/end.png')
    video_clip = ImageClip('./images/end.png')
    tts.save_to_file('Подписывайтесь и ставьте лайки!', './audios/end.mp3')
    tts.runAndWait()
    audio_clip = AudioFileClip(f'./audios/end.mp3', fps=44100).fx(afx.volumex, 1.5)
    video_clip = video_clip.set_audio(audio_clip)
    video_clip = video_clip.set_duration(audio_clip.duration)
    clips.append(video_clip)
    durations.append(audio_clip.duration)
    first_clip = CompositeVideoClip(
        [
            clips[0]
            .set_pos("center")
            .fx(transfx.slide_out, duration=EFFECT_DURATION, side="left")
        ]
    ).set_start(0)

    last_clip = (
        CompositeVideoClip(
            [
                clips[-1]
                .set_pos("center")
                .fx(transfx.slide_in, duration=EFFECT_DURATION, side="right")
            ]
        )
        .set_start(sum([j for j in durations[:-1]]) - EFFECT_DURATION * (len(durations) - 1))
    )

    videos = (
        [first_clip]
        + [
            (
                CompositeVideoClip(
                    [
                        clip.set_pos("center").fx(
                            transfx.slide_in, duration=EFFECT_DURATION, side="right"
                        )
                    ]
                )
                .set_start(sum([j for j in durations[:idx]]) - EFFECT_DURATION * idx)
                .fx(transfx.slide_out, duration=EFFECT_DURATION, side="left")
            )
            for idx, clip in enumerate(clips[1:-1], start=1)
        ]
        + [last_clip]
    )

    video = CompositeVideoClip(videos)
    print(f'Длина: {round(video.duration / 60, 2)} минут')

    time.sleep(15)
    video.write_videofile("video.mp4", fps=60, remove_temp=True, codec="libx264", audio_codec="aac", audio=True)
    time.sleep(10)
    for folderName, subfolders, filenames in os.walk('./audios'):
        for filename in filenames:
            if 'transition' not in filename:
                os.remove(os.path.join(folderName, filename))
    for folderName, subfolders, filenames in os.walk('./images'):
        for filename in filenames:
            if 'askreddit' not in filename and 'preview' not in filename and 'start' not in filename:
                os.remove(os.path.join(folderName, filename))


if __name__ == '__main__':
    upvote()
