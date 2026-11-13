# -*- coding: utf-8 -*-
"""Génère une vidéo de démonstration VOLTIS (images + narration française)."""
from __future__ import annotations

import asyncio
import subprocess
import textwrap
from pathlib import Path

import edge_tts
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SHOTS = ROOT / "screenshots"
OUT = ROOT / "videos"
WORK = ROOT / "videos" / "_work"
OUT.mkdir(exist_ok=True)
WORK.mkdir(exist_ok=True)

W, H = 1600, 900
NAVY = (10, 31, 60)
AMBER = (245, 179, 1)
TEAL = (22, 166, 161)
WHITE = (255, 255, 255)
MUTED = (200, 215, 230)
FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_SEMI = "C:/Windows/Fonts/seguisb.ttf"
FONT_REG = "C:/Windows/Fonts/segoeui.ttf"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", size)


def title_card() -> Image.Image:
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    d.ellipse((1180, -220, 1820, 420), fill=(18, 58, 96))
    d.ellipse((1320, 560, 1760, 1000), fill=(15, 49, 85))
    logo = Image.open(ASSETS / "logo.png").convert("RGBA")
    logo.thumbnail((520, 140))
    img.paste(logo, (80, 70), logo)
    d.text((80, 280), "MINI-PROJET FINAL · 2026", font=font(FONT_SEMI, 22), fill=AMBER)
    d.text((80, 330), "VOLTIS", font=font(FONT_BOLD, 92), fill=WHITE)
    d.text((80, 440), "Le hub agentique du réseau électrique", font=font(FONT_SEMI, 47), fill=WHITE)
    d.text((80, 530), "MCP · A2A · RAG · LangGraph · Dashboard 8033", font=font(FONT_REG, 28), fill=MUTED)
    for index, label in enumerate(["MCP", "A2A", "RAG", "Reflexion"]):
        x = 80 + index * 220
        d.rounded_rectangle((x, 640, x + 190, 690), radius=25, fill=(22, 58, 93), outline=(42, 82, 119))
        d.text((x + 95, 665), label, font=font(FONT_SEMI, 20), fill=WHITE, anchor="mm")
    d.text((80, 820), "Version 1.0.0 · 12 novembre 2026", font=font(FONT_REG, 20), fill=(150, 175, 200))
    return img


def end_card() -> Image.Image:
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    d.ellipse((1180, -220, 1820, 420), fill=(18, 58, 96))
    logo = Image.open(ASSETS / "logo.png").convert("RGBA")
    logo.thumbnail((420, 115))
    img.paste(logo, (80, 70), logo)
    d.text((80, 270), "CONCLUSION", font=font(FONT_SEMI, 22), fill=AMBER)
    d.text((80, 315), "Un agent qui décide,", font=font(FONT_BOLD, 60), fill=WHITE)
    d.text((80, 390), "cite et se corrige.", font=font(FONT_BOLD, 60), fill=WHITE)
    d.text((80, 500), "MCP · 10 outils      A2A · 4 agents      Reflexion · 6,48 → 9,40",
           font=font(FONT_REG, 26), fill=MUTED)
    d.text((80, 620), "Merci · Questions ?", font=font(FONT_SEMI, 40), fill=AMBER)
    d.text((80, 690), "localhost:8033 · Documentation et présentation incluses",
           font=font(FONT_REG, 22), fill=(150, 175, 200))
    return img


def fit_image(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGB")
    # crop the browser viewport to 16:9 (keep the top)
    target_ratio = W / H
    ratio = img.width / img.height
    if ratio > target_ratio:
        new_w = int(img.height * target_ratio)
        left = (img.width - new_w) // 2
        img = img.crop((left, 0, left + new_w, img.height))
    else:
        new_h = int(img.width / target_ratio)
        img = img.crop((0, 0, img.width, new_h))
    return img.resize((W, H), Image.LANCZOS)


SEGMENTS = [
    ("title", None, "Bienvenue dans VOLTIS, le hub agentique du réseau électrique. Cette démonstration présente une plateforme qui relie les données du réseau, les procédures internes et quatre agents spécialisés.", 0),
    ("home", SHOTS / "home.png", "Le dashboard 8033 offre une vue d'ensemble : consommation, pointe, mix de production, qualité de service et incidents récents. Le menu donne accès à l'assistant, au playground MCP, à l'orchestration A2A et aux statistiques.", 1),
    ("assistant", SHOTS / "assistant.png", "Dans l'assistant, une question en français déclenche le workflow LangGraph. L'agent planifie, recherche les documents, appelle les outils MCP, rédige une réponse chiffrée, la critique puis la raffine. Le score passe de 6,4 à 9,3 et chaque affirmation est sourcée.", 2),
    ("a2a", SHOTS / "a2a.png", "L'orchestrateur A2A découvre les AgentCards, sélectionne trois spécialistes et délègue en parallèle avec un correlation_id. Les artefacts sont agrégés en une réponse unique et tracés dans le journal.", 3),
    ("stats", SHOTS / "stats.png", "La page statistiques explore huit régions, 42,3 térawattheures, 72 incidents et le benchmark Reflexion. Les mêmes données alimentent les agents et la documentation.", 4),
    ("mcp", SHOTS / "mcp.png", "Le serveur MCP expose dix outils standards en JSON-RPC : KPI, incidents, prévision, facturation, recherche documentaire et économies d'énergie.", 5),
    ("architecture", SHOTS / "architecture.png", "Docker Compose lance le dashboard, le serveur MCP et l'orchestrateur A2A avec des healthchecks et des volumes partagés. Une seule commande suffit pour reproduire l'environnement.", 6),
    ("end", None, "VOLTIS démontre qu'une plateforme agentique peut être utile, traçable et démontrable. Merci de votre attention.", 7),
]


async def synthesize(text: str, path: Path) -> None:
    communicate = edge_tts.Communicate(text, "fr-FR-DeniseNeural", rate="+3%")
    await communicate.save(str(path))


def run_ffmpeg(args: list[str]) -> None:
    subprocess.run([FFMPEG, "-y", *args], check=True, capture_output=True)


def main() -> None:
    print("Génération des cartes…")
    title_card().save(WORK / "title.png")
    end_card().save(WORK / "end.png")
    for name, path, _, _ in SEGMENTS:
        if path is not None and path.exists():
            fit_image(path).save(WORK / f"{name}.png")

    print("Synthèse vocale…")
    for name, _, text, index in SEGMENTS:
        asyncio.run(synthesize(text, WORK / f"{name}.mp3"))
        print(f"  · {name}")

    print("Encodage des segments…")
    concat_lines = []
    for name, _, _, index in SEGMENTS:
        image = WORK / f"{name}.png"
        audio = WORK / f"{name}.mp3"
        segment = WORK / f"seg_{index:02d}.mp4"
        run_ffmpeg([
            "-loop", "1", "-i", str(image), "-i", str(audio),
            "-c:v", "libx264", "-tune", "stillimage", "-r", "30",
            "-c:a", "aac", "-b:a", "160k", "-pix_fmt", "yuv420p",
            "-vf", f"scale={W}:{H},format=yuv420p",
            "-shortest", "-movflags", "+faststart", str(segment),
        ])
        concat_lines.append(f"file '{segment.as_posix()}'")
        print(f"  · {name}")

    list_file = WORK / "concat.txt"
    list_file.write_text("\n".join(concat_lines), encoding="utf-8")
    final = OUT / "VOLTIS_Demo.mp4"
    run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(final)])
    print("Vidéo générée :", final, f"{final.stat().st_size / (1024*1024):.1f} Mo")


if __name__ == "__main__":
    main()
