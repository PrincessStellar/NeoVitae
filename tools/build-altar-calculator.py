import base64
import json
import math
import re
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "src" / "generated" / "resources"
MAIN = ROOT / "src" / "main" / "resources"
JAVA = ROOT / "src" / "main" / "java" / "com" / "breakinblocks" / "neovitae"
OUT = ROOT / "calculator"
ADDONS = OUT / "addons"

TIER_ORDER = ["weak", "apprentice", "mage", "master", "archmage", "transcendent"]

RUNE_ORDER = [
    "speed",
    "efficiency",
    "sacrifice",
    "sacrifice_self",
    "capacity",
    "capacity_augmented",
    "dislocation",
    "orb",
    "acceleration",
    "charging",
]

MOB_MAX_HEALTH = {
    "allay": 20,
    "armadillo": 12,
    "axolotl": 14,
    "bat": 6,
    "bee": 10,
    "blaze": 20,
    "bogged": 16,
    "breeze": 30,
    "camel": 32,
    "cat": 10,
    "cave_spider": 12,
    "chicken": 4,
    "cod": 3,
    "cow": 10,
    "creeper": 20,
    "dolphin": 10,
    "drowned": 20,
    "elder_guardian": 80,
    "enderman": 40,
    "endermite": 8,
    "evoker": 24,
    "fox": 10,
    "frog": 10,
    "ghast": 10,
    "giant": 100,
    "glow_squid": 10,
    "goat": 10,
    "guardian": 30,
    "hoglin": 40,
    "husk": 20,
    "illusioner": 32,
    "iron_golem": 100,
    "mooshroom": 10,
    "ocelot": 10,
    "panda": 20,
    "parrot": 6,
    "phantom": 20,
    "pig": 10,
    "piglin": 16,
    "piglin_brute": 50,
    "pillager": 24,
    "polar_bear": 30,
    "pufferfish": 3,
    "rabbit": 3,
    "ravager": 100,
    "salmon": 3,
    "sheep": 8,
    "shulker": 30,
    "silverfish": 8,
    "skeleton": 20,
    "sniffer": 14,
    "snow_golem": 4,
    "spider": 16,
    "squid": 10,
    "stray": 20,
    "tadpole": 6,
    "tropical_fish": 3,
    "turtle": 30,
    "vex": 14,
    "villager": 20,
    "vindicator": 24,
    "wandering_trader": 20,
    "warden": 500,
    "witch": 26,
    "wither_skeleton": 20,
    "wolf": 8,
    "zoglin": 40,
    "zombie": 20,
    "zombie_villager": 20,
    "zombified_piglin": 20,
}


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def find_resource(rel):
    for base in (MAIN, GEN):
        p = base / rel
        if p.exists():
            return p
    return None


LANG = load_json(GEN / "assets" / "neovitae" / "lang" / "en_us.json")
TEXTURES = {}


def display_name(ident):
    ns, _, path = ident.lstrip("#").partition(":")
    for kind in ("item", "block", "entity"):
        name = LANG.get(f"{kind}.{ns}.{path}")
        if name:
            song = LANG.get(f"jukebox_song.{ns}.{path}")
            if song:
                return f"{name}: {song.split(' - ', 1)[-1]}"
            return name
    return " ".join(w.capitalize() for w in re.split(r"[_/]", path))


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def add_texture(key, path):
    if key in TEXTURES:
        return key
    w, h = png_size(path)
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    TEXTURES[key] = {"src": f"data:image/png;base64,{data}", "w": w, "h": h}
    return key


def texture_file(tex_id):
    ns, _, path = tex_id.partition(":")
    if not path:
        ns, path = "minecraft", ns
    return find_resource(Path("assets") / ns / "textures" / f"{path}.png")


def texture_key(tex_id):
    p = texture_file(tex_id)
    if not p:
        return None
    return add_texture(tex_id.split(":", 1)[-1].replace("/", "_"), p)


def add_texture_bytes(key, data, w, h):
    TEXTURES[key] = {"src": f"data:image/png;base64,{base64.b64encode(data).decode('ascii')}", "w": w, "h": h}
    return key


def read_png(path):
    raw = path.read_bytes()
    pos = 8
    idat = b""
    while pos < len(raw):
        length, kind = struct.unpack(">I4s", raw[pos : pos + 8])
        chunk = raw[pos + 8 : pos + 8 + length]
        if kind == b"IHDR":
            w, h, depth, color, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
        elif kind == b"IDAT":
            idat += chunk
        pos += 12 + length
    channels = {2: 3, 6: 4}.get(color)
    if depth != 8 or not channels:
        raise ValueError(f"{path.name}: only 8-bit RGB/RGBA PNGs are supported")
    data = zlib.decompress(idat)
    passes = [(0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8), (2, 0, 4, 4), (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2)] if interlace else [(0, 0, 1, 1)]
    pixels = [(0, 0, 0, 0)] * (w * h)
    pos = 0
    for x0, y0, dx, dy in passes:
        pw = (w - x0 + dx - 1) // dx
        ph = (h - y0 + dy - 1) // dy
        if pw <= 0 or ph <= 0:
            continue
        stride = pw * channels
        prev = bytearray(stride)
        for row in range(ph):
            f = data[pos]
            line = bytearray(data[pos + 1 : pos + 1 + stride])
            pos += 1 + stride
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                if f == 1:
                    line[i] = (line[i] + a) & 255
                elif f == 2:
                    line[i] = (line[i] + b) & 255
                elif f == 3:
                    line[i] = (line[i] + (a + b) // 2) & 255
                elif f == 4:
                    pr = a + b - c
                    pa, pb, pc = abs(pr - a), abs(pr - b), abs(pr - c)
                    line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
            prev = line
            for col in range(pw):
                px = line[col * channels : (col + 1) * channels]
                pixels[(y0 + row * dy) * w + x0 + col * dx] = tuple(px) if channels == 4 else (*px, 255)
    return w, h, pixels


def write_png(w, h, pixels):
    raw = b"".join(b"\x00" + bytes(v for px in pixels[y * w : (y + 1) * w] for v in px) for y in range(h))

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)

    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def load_obj(path):
    verts, uvs, faces = [], [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "v":
            verts.append(tuple(float(v) for v in parts[1:4]))
        elif parts[0] == "vt":
            uvs.append((float(parts[1]), float(parts[2])))
        elif parts[0] == "f":
            corners = []
            for ref in parts[1:]:
                idx = ref.split("/")
                corners.append((verts[int(idx[0]) - 1], uvs[int(idx[1]) - 1] if len(idx) > 1 and idx[1] else (0.0, 0.0)))
            faces.append(corners)
    return faces


def render_obj(faces, texture, size, flip_v):
    tw, th, tex = texture
    ss = 3
    full = size * ss
    cos30, sin30, inv2 = math.cos(math.pi / 6), math.sin(math.pi / 6), 1 / math.sqrt(2)

    def project(v):
        x, y, z = v[0] - 0.5, v[1] - 0.5, v[2] - 0.5
        a, b = (x - z) * inv2, (x + z) * inv2
        return a, -(y * cos30 - b * sin30), b * cos30 + y * sin30

    tris = []
    for corners in faces:
        pts = [(project(v), uv, v) for v, uv in corners]
        for i in range(1, len(pts) - 1):
            tris.append((pts[0], pts[i], pts[i + 1]))
    xs = [p[0][0] for t in tris for p in t]
    ys = [p[0][1] for t in tris for p in t]
    span = max(max(xs) - min(xs), max(ys) - min(ys)) * 1.08
    ox = (min(xs) + max(xs)) / 2 - span / 2
    oy = (min(ys) + max(ys)) / 2 - span / 2
    scale = full / span
    color = [None] * (full * full)
    depth = [-1e9] * (full * full)
    for t in tris:
        (p0, uv0, w0), (p1, uv1, w1), (p2, uv2, w2) = t
        e1 = [w1[i] - w0[i] for i in range(3)]
        e2 = [w2[i] - w0[i] for i in range(3)]
        n = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
        mag = math.sqrt(sum(c * c for c in n)) or 1
        nx, ny, nz = (c / mag for c in n)
        if (nx + nz) * inv2 * cos30 + ny * sin30 <= 0.001:
            continue
        shade = nx * nx * 0.6 + nz * nz * 0.8 + ny * ny * (1.0 if ny > 0 else 0.5)
        sx = [(p[0] - ox) * scale for p in (p0, p1, p2)]
        sy = [(p[1] - oy) * scale for p in (p0, p1, p2)]
        area = (sx[1] - sx[0]) * (sy[2] - sy[0]) - (sx[2] - sx[0]) * (sy[1] - sy[0])
        if abs(area) < 1e-9:
            continue
        for py in range(max(0, int(min(sy))), min(full, int(max(sy)) + 1)):
            cy = py + 0.5
            for px in range(max(0, int(min(sx))), min(full, int(max(sx)) + 1)):
                cx = px + 0.5
                l1 = ((sx[2] - cx) * (sy[0] - cy) - (sx[0] - cx) * (sy[2] - cy)) / area
                l2 = ((sx[0] - cx) * (sy[1] - cy) - (sx[1] - cx) * (sy[0] - cy)) / area
                l0 = 1 - l1 - l2
                if min(l0, l1, l2) < -1e-6:
                    continue
                d = l0 * p0[2] + l1 * p1[2] + l2 * p2[2]
                i = py * full + px
                if d <= depth[i]:
                    continue
                u = l0 * uv0[0] + l1 * uv1[0] + l2 * uv2[0]
                v = l0 * uv0[1] + l1 * uv1[1] + l2 * uv2[1]
                tx = min(tw - 1, max(0, int(u * tw)))
                ty = min(th - 1, max(0, int((1 - v if flip_v else v) * th)))
                r, g, b, a = tex[ty * tw + tx]
                if a < 8:
                    continue
                depth[i] = d
                color[i] = (r * shade, g * shade, b * shade)
    out = []
    for y in range(size):
        for x in range(size):
            acc = [0.0, 0.0, 0.0]
            hits = 0
            for dy in range(ss):
                for dx in range(ss):
                    c = color[(y * ss + dy) * full + x * ss + dx]
                    if c:
                        hits += 1
                        for k in range(3):
                            acc[k] += c[k]
            if hits:
                out.append((*(min(255, round(acc[k] / hits)) for k in range(3)), round(255 * hits / (ss * ss))))
            else:
                out.append((0, 0, 0, 0))
    return out


def obj_block_icon(model_id, size):
    model = load_model(model_id)
    ns, _, obj = model["model"].partition(":")
    faces = load_obj(find_resource(Path("assets") / ns / obj))
    texture = read_png(texture_file(model["textures"]["default"]))
    pixels = render_obj(faces, texture, size, model.get("flip_v", False))
    return add_texture_bytes(f"{model_id.split(':', 1)[-1].replace('/', '_')}_icon", write_png(size, size, pixels), size, size)


def first_model_ref(node):
    if isinstance(node, dict):
        if node.get("type") in ("minecraft:model", "model") and isinstance(node.get("model"), str):
            return node["model"]
        for v in node.values():
            found = first_model_ref(v)
            if found:
                return found
    elif isinstance(node, list):
        for v in node:
            found = first_model_ref(v)
            if found:
                return found
    return None


def load_model(model_id):
    ns, _, path = model_id.partition(":")
    if not path:
        ns, path = "minecraft", ns
    p = find_resource(Path("assets") / ns / "models" / f"{path}.json")
    return load_json(p) if p else None


def model_texture(model_id, depth=0):
    if depth > 6:
        return None
    model = load_model(model_id)
    if not model:
        return None
    textures = model.get("textures", {})
    for key in ("layer0", "all", "base", "top", "front", "side", "texture", "particle"):
        tex = textures.get(key)
        if isinstance(tex, str) and not tex.startswith("#"):
            return tex
    parent = model.get("parent")
    if parent and not parent.startswith("minecraft:") and not parent.startswith("builtin/"):
        return model_texture(parent, depth + 1)
    return None


def item_icon(ident):
    if not ident.startswith("neovitae:"):
        return None
    path = ident.split(":", 1)[1]
    item_def = find_resource(Path("assets") / "neovitae" / "items" / f"{path}.json")
    if item_def:
        ref = first_model_ref(load_json(item_def))
        tex = model_texture(ref) if ref else None
        if tex and texture_file(tex):
            return texture_key(tex)
    for folder in ("item", "block"):
        p = find_resource(Path("assets") / "neovitae" / "textures" / folder / f"{path}.png")
        if p:
            return add_texture(f"{folder}_{path}", p)
    return None


def block_textures(block_id):
    model = load_model(f"{block_id.split(':')[0]}:block/{block_id.split(':')[1]}")
    textures = (model or {}).get("textures", {})
    base = textures.get("base") or textures.get("all") or textures.get("texture") or textures.get("particle")
    glow = textures.get("glow")
    if not base:
        base = f"{block_id.split(':')[0]}:block/{block_id.split(':')[1]}"
    return {
        "base": texture_key(base) if texture_file(base) else None,
        "glow": texture_key(glow) if glow and texture_file(glow) else None,
    }


def build_altar_model():
    model = load_model("neovitae:block/ara_vitae")
    size = model.get("texture_size", [16, 16])
    tex = texture_key(model["textures"]["0"])
    elements = []
    for e in model["elements"]:
        faces = {}
        for side, face in e["faces"].items():
            faces[side] = {"uv": face.get("uv", [0, 0, 16, 16]), "rotation": face.get("rotation", 0)}
        elements.append({"from": e["from"], "to": e["to"], "faces": faces})
    return {"texture": tex, "textureSize": size, "elements": elements}


def tag_values(tag):
    ns, _, path = tag.lstrip("#").partition(":")
    data = load_json(GEN / "data" / ns / "tags" / "block" / f"{path}.json")
    return [v if isinstance(v, str) else v["id"] for v in data["values"]]


def build_structure():
    positions = {}
    tiers = []
    for index, name in enumerate(TIER_ORDER):
        data = load_json(GEN / "data" / "neovitae" / "neovitae" / "altar_tier" / f"{name}.json")
        comps = data["components"]
        tiers.append(
            {
                "tier": index,
                "id": name,
                "runeBlocks": sum(1 for c in comps if c["valid"] == "#neovitae:altar/runes"),
                "upgradeSlots": sum(1 for c in comps if c.get("upgrade")),
            }
        )
        for c in comps:
            key = tuple(c["pos"])
            valid = c["valid"]
            if valid == "neovitae:ara_vitae":
                kind, material = "altar", None
            elif valid == "#neovitae:altar/runes":
                kind, material = "rune", None
            elif valid == "#neovitae:altar/pillars":
                kind, material = "pillar", None
            else:
                kind = "cap"
                material = tag_values(valid)[0] if valid.startswith("#") else valid
            entry = positions.get(key)
            if entry is None:
                entry = positions[key] = {
                    "p": list(key),
                    "kind": kind,
                    "from": index,
                    "upgradeFrom": None,
                    "material": material,
                    "optional": bool(c.get("optional")),
                }
            elif entry["kind"] != kind:
                raise SystemExit(f"Component at {key} changes kind between tiers")
            if c.get("upgrade") and entry["upgradeFrom"] is None:
                entry["upgradeFrom"] = index
    blocks = sorted(positions.values(), key=lambda b: (-b["p"][1], b["p"][0], b["p"][2]))
    materials = {}
    for b in blocks:
        if b["material"] and b["material"] not in materials:
            materials[b["material"]] = {"name": display_name(b["material"]), **block_textures(b["material"])}
    return tiers, blocks, materials


def build_runes():
    stats = load_json(GEN / "data" / "neovitae" / "data_maps" / "block" / "altar_rune_stats.json")["values"]
    runes = []
    for key in RUNE_ORDER:
        for reinforced in (False, True):
            block = f"neovitae:rune_2_{key}" if reinforced else f"neovitae:rune_{key}"
            if block not in stats:
                continue
            tex = block_textures(block)
            runes.append(
                {
                    "id": block,
                    "key": block.split(":")[1],
                    "type": key,
                    "reinforced": reinforced,
                    "name": display_name(block),
                    "texture": tex["base"],
                    "glow": tex["glow"],
                    "stats": stats[block],
                }
            )
    blank = block_textures("neovitae:rune_blank")
    return runes, {"name": display_name("neovitae:rune_blank"), "texture": blank["base"], "glow": blank["glow"]}


def build_orbs():
    stats = load_json(GEN / "data" / "neovitae" / "data_maps" / "item" / "blood_orb_stats.json")["values"]
    return [
        {
            "id": ident,
            "name": display_name(ident),
            "icon": item_icon(ident),
            "tier": v["tier"],
            "fillRate": v["fillRate"],
            "animaCapacity": v["animaCapacity"],
        }
        for ident, v in stats.items()
    ]


def build_recipes():
    recipes = []
    for f in sorted((GEN / "data" / "neovitae" / "recipe").rglob("*.json")):
        d = load_json(f)
        if d.get("type") != "neovitae:ara_vitae_recipe":
            continue
        out = d["output"]["id"]
        recipes.append(
            {
                "id": f.stem,
                "name": display_name(out),
                "icon": item_icon(out),
                "bloodNeeded": d["bloodNeeded"],
                "craftSpeed": d["craftSpeed"],
                "drainSpeed": d["drainSpeed"],
                "minTier": d["minTier"],
            }
        )
    recipes.sort(key=lambda r: (r["minTier"], r["name"]))
    return recipes


def build_mobs():
    values = load_json(GEN / "data" / "neovitae" / "data_maps" / "entity_type" / "entity_sacrifice_value.json")["values"]
    mobs = []
    for ident, v in values.items():
        path = ident.split(":", 1)[1]
        if ident.startswith("#") or path not in MOB_MAX_HEALTH:
            continue
        mobs.append(
            {
                "id": ident,
                "name": " ".join(w.capitalize() for w in path.split("_")),
                "evPerDamage": v["ev_per_damage"],
                "maxPerHit": v.get("max_ev_per_hit"),
                "maxHealth": MOB_MAX_HEALTH[path],
            }
        )
    mobs.sort(key=lambda m: m["name"])
    return mobs


def java_text(rel):
    return (JAVA / rel).read_text(encoding="utf-8")


def config_int(config, key, default):
    m = re.search(rf'"{key}",\s*(\d+)', config)
    return int(m.group(1)) if m else default


def java_const(java, name, default):
    m = re.search(rf"\b{name}\s*=\s*([0-9.]+)[FfDd]?;", java)
    return float(m.group(1)) if m else default


def build_rituals():
    stats = load_json(GEN / "data" / "neovitae" / "data_maps" / "neovitae" / "ritual" / "ritual_stats.json")["values"]
    config = java_text("ServerConfig.java")
    knife = java_text("ritual/types/RitualFeatheredKnife.java")

    def ritual(key):
        s = stats.get(f"neovitae:{key}", {})
        return {"refreshCost": s.get("refresh_cost", 0), "refreshTime": s.get("refresh_time", 20)}

    return {
        "wellOfSuffering": {**ritual("well_of_suffering"), "damage": 1.0},
        "featheredKnife": {
            **ritual("feathered_knife"),
            "evMultiplier": int(java_const(knife, "EV_MULTIPLIER", 4)),
            "healthPerUse": 1,
            "sentientBonus": 1.1,
        },
        "tormentNexus": {
            **ritual("torment_nexus"),
            "evPerKill": config_int(config, "ev_per_kill", 75),
            "maxEvPerOperation": config_int(config, "max_ev_per_operation", 8000),
            "evModifierPercent": config_int(config, "ev_modifier_percent", 100),
            "spawnCount": 4,
            "minSpawnDelay": 200,
            "maxSpawnDelay": 800,
        },
    }


def build_constants():
    java = java_text("common/blockentity/AltarConstants.java")
    config = java_text("ServerConfig.java")
    return {
        "baseTickRate": int(java_const(java, "BASE_TICK_RATE", 20)),
        "minTickRate": int(java_const(java, "MIN_TICK_RATE", 1)),
        "baseIoRate": java_const(java, "BASE_IO_RATE", 20),
        "chargeCapacityMinFactor": java_const(java, "CHARGE_CAPACITY_MIN_FACTOR", 0.5),
        "craftingCooldownTicks": int(java_const(java, "CRAFTING_COOLDOWN_TICKS", 30)),
        "selfSacrificeConversion": config_int(config, "self_sacrifice_conversion", 100),
        "bucket": 1000,
    }


VANILLA_TAGS = {
    "minecraft:stone_bricks": [
        "minecraft:stone_bricks",
        "minecraft:mossy_stone_bricks",
        "minecraft:cracked_stone_bricks",
        "minecraft:chiseled_stone_bricks",
    ],
}

TRANQUILITY_EXAMPLES = {
    "#minecraft:dirt": "any dirt-type block",
    "#minecraft:flowers": "any flower",
    "#minecraft:small_flowers": "any small flower",
    "#minecraft:tall_flowers": "any tall flower",
    "#minecraft:leaves": "any leaves",
    "#minecraft:logs": "any log",
}

TYPE_COLORS = {
    "earthen": "#7a5634",
    "plant": "#4f9a3c",
    "crop": "#c9b03a",
    "tree": "#2f6b2a",
    "water": "#2f63c9",
    "fire": "#e0682a",
    "lava": "#d8401c",
}


def resolve_block_tag(tag, seen=None):
    seen = seen or set()
    if tag in seen:
        return set()
    seen.add(tag)
    if tag in VANILLA_TAGS:
        return set(VANILLA_TAGS[tag])
    ns, _, path = tag.partition(":")
    p = GEN / "data" / ns / "tags" / "block" / f"{path}.json"
    if not p.exists():
        return set()
    out = set()
    for v in load_json(p)["values"]:
        ident = v if isinstance(v, str) else v["id"]
        if ident.startswith("#"):
            out |= resolve_block_tag(ident[1:], seen)
        else:
            out.add(ident)
    return out


def java_double_array(java, name):
    m = re.search(rf"{name}\s*=\s*new double\[\]\s*\{{([^}}]*)\}}", java)
    return [float(x) for x in m.group(1).split(",")]


def java_int_array(java, name):
    m = re.search(rf"{name}\s*=\s*new int\[\]\s*\{{([^}}]*)\}}", java)
    return [int(x) for x in m.group(1).split(",")]


def build_garden():
    handler = java_text("incense/IncenseAltarHandler.java")
    altar = java_text("common/blockentity/IncenseAltarBlockEntity.java")
    levels = {}
    for level in range(11):
        for block in resolve_block_tag(f"neovitae:incense_path/level_{level}"):
            levels[block] = max(levels.get(block, -1), level)
    paths = []
    merged = set(VANILLA_TAGS["minecraft:stone_bricks"])
    if merged & set(levels):
        level = max(levels[b] for b in merged if b in levels)
        paths.append({"id": "minecraft:stone_bricks", "name": "Stone Bricks (any variant)", "level": level, "texture": None})
    for block, level in levels.items():
        if block in merged:
            continue
        tex = block_textures(block)["base"] if block.startswith("neovitae:") else None
        paths.append({"id": block, "name": display_name(block), "level": level, "texture": tex})
    paths.sort(key=lambda p: (p["level"], p["name"]))

    datamap = load_json(GEN / "data" / "neovitae" / "data_maps" / "block" / "tranquility.json")["values"]
    groups = {}
    for ident, v in datamap.items():
        value = v.get("value", 1.0)
        key = (v["type"], value)
        if ident.startswith("#"):
            members = resolve_block_tag(ident[1:])
            if not members and ident not in TRANQUILITY_EXAMPLES:
                continue
            label = TRANQUILITY_EXAMPLES.get(ident) or ", ".join(sorted(display_name(m) for m in members))
        else:
            label = display_name(ident)
        groups.setdefault(key, []).append((label, ident))
    blocks = []
    type_order = list(TYPE_COLORS)
    for (kind, value), items in sorted(groups.items(), key=lambda kv: (type_order.index(kv[0][0]), -kv[0][1])):
        labels = sorted({label for label, _ in items})
        texture = None
        for _, ident in items:
            if ident.startswith("neovitae:"):
                texture = block_textures(ident)["base"]
        blocks.append(
            {
                "key": f"{kind}_{str(value).replace('.', '_')}",
                "type": kind,
                "value": value,
                "examples": labels,
                "texture": texture,
                "color": TYPE_COLORS[kind],
            }
        )
    return {
        "bonuses": java_double_array(handler, "INCENSE_BONUSES"),
        "tranquilityRequired": java_double_array(handler, "TRANQUILITY_REQUIRED"),
        "roadsRequired": java_int_array(handler, "ROADS_REQUIRED"),
        "maxRoadDistance": int(java_const(altar, "MAX_ROAD_DISTANCE", 12)),
        "layers": 3,
        "paths": paths,
        "blocks": blocks,
        "types": [{"type": t, "color": c} for t, c in TYPE_COLORS.items()],
        "incenseAltarIcon": obj_block_icon("neovitae:block/incense_altar", 96),
    }


def build_addons():
    addons = load_json(ADDONS / "addons.json")
    for entry in addons.get("runes", []) + addons.get("orbs", []):
        icon = entry.pop("icon", None)
        if icon:
            key = add_texture(f"addon_{Path(icon).stem}", ADDONS / icon)
            entry["texture" if entry in addons.get("runes", []) else "icon"] = key
    return addons


def mod_version():
    m = re.search(r"^mod_version\s*=\s*(\S+)", (ROOT / "gradle.properties").read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else None


def main():
    tiers, blocks, materials = build_structure()
    runes, blank = build_runes()
    addons = build_addons()
    orbs = build_orbs() + addons.get("orbs", [])
    orbs.sort(key=lambda o: (o["tier"], o["fillRate"]))
    data = {
        "modVersion": mod_version(),
        "constants": build_constants(),
        "tiers": tiers,
        "blocks": blocks,
        "materials": materials,
        "altarModel": build_altar_model(),
        "runes": runes,
        "blankRune": blank,
        "addonRunes": addons.get("runes", []),
        "orbs": orbs,
        "recipes": build_recipes(),
        "mobs": build_mobs(),
        "rituals": build_rituals(),
        "garden": build_garden(),
        "textures": TEXTURES,
    }
    with open(OUT / "data.js", "w", encoding="utf-8", newline="\n") as f:
        f.write("window.ALTAR_DATA = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    for stale in (OUT / "data.json", OUT / "icons"):
        if stale.is_dir():
            for child in stale.iterdir():
                child.unlink()
            stale.rmdir()
        elif stale.exists():
            stale.unlink()
    print(
        f"Wrote {OUT / 'data.js'}: {len(tiers)} tiers, {len(blocks)} structure blocks, {len(runes)} runes, "
        f"{len(data['addonRunes'])} addon runes, {len(orbs)} orbs, {len(data['recipes'])} recipes, "
        f"{len(data['mobs'])} mobs, {len(TEXTURES)} textures, {(OUT / 'data.js').stat().st_size // 1024} KB"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
