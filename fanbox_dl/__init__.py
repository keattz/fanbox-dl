import sys
from collections import Counter
from pathlib import Path
from typing import Any

import click
import requests


def download(
    url: str, dest: Path, clobber: bool, dry_run: bool, session_id: str
) -> None:
    if dry_run:
        print(f"{url} => {dest}")
        pass
    else:
        req = get(url, session_id)
        file = Path(dest)
        file.parent.mkdir(parents=True, exist_ok=True)
        if clobber or not file.exists():
            with open(file, "wb") as f:
                f.write(req.content)


def get(url: str, session_id: str) -> requests.Response:
    return requests.get(
        url,
        cookies={"FANBOXSESSID": session_id},
        headers={"Origin": "https://fanbox.cc"},
    )


def get_post(post_id: str, session_id: str) -> Any:
    url = f"https://api.fanbox.cc/post.info?postId={post_id}"

    req = get(url, session_id)
    req.raise_for_status()

    try:
        data = req.json()
    except ValueError:
        return None
    if "body" not in data:
        return None
    return data["body"]


def get_posts(creator: str, session_id: str) -> Any:
    limit = 300
    url = f"https://api.fanbox.cc/post.listCreator?creatorId={creator}&limit={limit}"

    req = get(url, session_id)
    req.raise_for_status()

    try:
        data = req.json()
    except ValueError:
        return None
    if "body" not in data or "items" not in data["body"]:
        return None
    if "nextUrl" in data["body"] and data["body"]["nextUrl"] is not None:
        print(
            f"Warning: Only the {limit} newest posts in the fanbox are downloaded.",
            file=sys.stderr,
        )
    return data["body"]["items"]


@click.command()
@click.option("-c", "--cookie-file", required=True)
@click.option("-o", "--output", default=".", show_default=True)
@click.option("--clobber/--no-clobber", default=False, show_default=True)
@click.option("--dry-run", is_flag=True, show_default=True)
@click.argument("creator")
def main(
    cookie_file: str, output: str, clobber: bool, dry_run: bool, creator: str
) -> None:
    with open(cookie_file) as f:
        session_id = f.read().strip()

    posts = get_posts(creator, session_id)
    if posts is None:
        print(f"Error: Couldn't fetch posts of {creator}", file=sys.stderr)
        sys.exit(1)

    get_prefix = (
        lambda post: f'{post["creatorId"]}/{post["publishedDatetime"].split("T")[0]}'
    )

    prefix_counter = Counter()
    for post in posts:
        prefix_counter[get_prefix(post)] += 1

    prefix_i = 0
    for i, post in enumerate(posts):
        prefix = get_prefix(post)
        if prefix_counter[prefix] > 1:
            prefix_i += 1
        else:
            prefix_i = 0
        if prefix_i:
            prefix += f"_{prefix_i}"

        print(
            f"Fetching post {post['id']} as {prefix} ({i + 1}/{len(posts)})",
            file=sys.stderr,
        )
        data = get_post(post["id"], session_id)
        if data is None or "body" not in data or not data["body"]:
            print(f"Warning: Couldn't fetch post {post['id']}", file=sys.stderr)
            continue

        # metadata_path = dest_dir / "metadata.json"
        # if clobber or not metadata_path.exists():
        #    with open(metadata_path, "w") as f:
        #        json.dump(data, f)

        urls = (
            [data["coverImageUrl"]]
            + [x["originalUrl"] for x in data["body"].get("images", [])]
            + [x["originalUrl"] for x in data["body"].get("imageMap", {}).values()]
            + [x["url"] for x in data["body"].get("files", [])]
            + [x["url"] for x in data["body"].get("fileMap", {}).values()]
        )
        images = []
        n_pad = len(str(len(urls)))
        for n, url in enumerate(urls):
            dest = Path(output, f'{prefix}_{n:0{n_pad}}.{url.split(".")[-1]}')
            images.append({"dest": dest, "url": url})

        for image in images:
            download(image["url"], image["dest"], clobber, dry_run, session_id)
