"""make_scrapbook.py — scenes.json -> scrapbook.jsx for EffectCraft.
Midnight scrapbook: gradient night bg with drifting fractal-noise haze, cream paper card (rounded rect shape,
drop shadow, washi tape, slow sway), die-cut stickers with drop shadows that enter on the beat
(pop / spin / drop / slide_l / slide_r / fade), sway idly (expression), pop out at scene end; card bump on every
scene change; hand-lettered caption revealed through a text-animator range selector; soft Glow; @handle.
usage: python3 make_scrapbook.py scenes.json song.wav out.jsx [max_seconds]"""
import sys, json, os
sys.path.insert(0, '/home/claude/raft/craftreel')
from beats import onsets

W, H = 1080, 1920
CX, CY, CW, CH = 540, 905, 960, 880          # card centre / size
CAP_Y = 1470


def js(v): return json.dumps(v, ensure_ascii=False)


def snap(t, on, win=0.25):
    near = [o for o in on if abs(o - t) <= win]
    return min(near, key=lambda o: abs(o - t)) if near else t


def build(spec, song, maxdur):
    on, _, _ = onsets(song)
    scenes = [s for s in spec['scenes'] if s['t'] < maxdur]
    dur = min(maxdur, scenes[-1]['t'] + scenes[-1]['dur'])
    L = []; a = L.append
    a(f'var c = app.project.items.addComp("Scrapbook", {W}, {H}, 1, {dur}, 30);')
    a('function imp(p){ return app.project.importFile(new ImportOptions(new File(p))); }')
    a('function P(l, n){ return l.property("ADBE Transform Group").property(n); }')
    a(f'var aud = c.layers.add(imp({js(os.path.abspath(song))})); aud.outPoint = {dur};')
    # --- background: night gradient + drifting haze
    a(f'var bg = c.layers.addSolid([0.04,0.05,0.13], "Night", {W}, {H}, 1, {dur});')
    a('var rp = bg.Effects.addProperty("ADBE Ramp"); rp.property("Start Color").setValue([0.03,0.05,0.16]); rp.property("End Color").setValue([0.20,0.07,0.24]);')
    a(f'rp.property("Start of Ramp").setValue([540,0]); rp.property("End of Ramp").setValue([540,{H}]);')
    a(f'var hz = c.layers.addSolid([0,0,0], "Haze", {W}, {H}, 1, {dur}); var fn = hz.Effects.addProperty("ADBE Fractal Noise");')
    a('fn.property("Evolution").expression = "time*40"; P(hz,"ADBE Opacity").setValue(14); hz.blendingMode = BlendingMode.SCREEN;')
    # --- card
    a('function rect(layer, w, h, r, col){ var g = layer.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").property("ADBE Vectors Group");'
      ' var q = g.addProperty("ADBE Vector Shape - Rect"); q.property("ADBE Vector Rect Size").setValue([w,h]); q.property("ADBE Vector Rect Roundness").setValue(r);'
      ' g.addProperty("ADBE Vector Graphic - Fill").property("ADBE Vector Fill Color").setValue(col); }')
    a(f'var card = c.layers.addShape(); card.name = "Card"; rect(card, {CW}, {CH}, 34, [0.94,0.88,0.77]); P(card,"ADBE Position").setValue([{CX},{CY}]);')
    a('var cds = card.Effects.addProperty("ADBE Drop Shadow"); cds.property("Distance").setValue(18); cds.property("Softness").setValue(40); cds.property("Opacity").setValue(60);')
    a('var nz = card.Effects.addProperty("ADBE Noise"); nz.property(1).setValue(7);')
    a('P(card,"ADBE Rotate Z").expression = "Math.sin(time*0.9)*0.8";')
    a('var cs = P(card,"ADBE Scale");')
    for s in scenes:
        t = snap(s['t'], on, 0.2)
        a(f'cs.setValueAtTime({round(max(0, t), 3)}, [96,96]); cs.setValueAtTime({round(t + 0.22, 3)}, [101,101]); cs.setValueAtTime({round(t + 0.4, 3)}, [100,100]);')
    for k, (tx, ty, tr) in enumerate([(CX - CW / 2 + 70, CY - CH / 2 + 10, -38), (CX + CW / 2 - 70, CY - CH / 2 + 10, 38)]):
        a(f'var tp{k} = c.layers.addShape(); rect(tp{k}, 190, 54, 4, [0.93,0.55,0.62]); P(tp{k},"ADBE Position").setValue([{tx},{ty}]);'
          f' P(tp{k},"ADBE Rotate Z").setValue({tr}); P(tp{k},"ADBE Opacity").setValue(78);')
    # --- stickers
    n = 0
    for si, s in enumerate(scenes):
        end = min(dur, s['t'] + s['dur'])
        for st in s['stickers']:
            t0 = 0.0 if (si == 0 and n == 0) else snap(s['t'] + st['at'], on)
            t0 = round(min(t0, end - 0.5), 3)
            px = CX - CW / 2 + st['x'] * CW; py = CY - CH / 2 + st['y'] * CH
            v = f's{n}'
            a(f'var {v} = c.layers.add(imp({js(os.path.abspath(st["src"]))})); {v}.inPoint = {t0}; {v}.outPoint = {round(end, 3)};')
            a(f'var w{n} = {st["w"] * CW} / {v}.source.width * 100; var Sc{n} = P({v},"ADBE Scale"); var Po{n} = P({v},"ADBE Position"); var Ro{n} = P({v},"ADBE Rotate Z");')
            a(f'Po{n}.setValue([{px:.1f},{py:.1f}]); Ro{n}.setValue({st["rot"]});')
            kind = st['in']
            if si == 0 and n == 0:                                   # hook: first sticker already on frame 0
                a(f'Sc{n}.setValue([w{n},w{n}]);')
            elif kind == 'pop':
                a(f'Sc{n}.setValueAtTime({t0}, [0,0]); Sc{n}.setValueAtTime({t0 + 0.18:.3f}, [w{n}*1.18,w{n}*1.18]); Sc{n}.setValueAtTime({t0 + 0.32:.3f}, [w{n},w{n}]);')
            elif kind == 'spin':
                a(f'Sc{n}.setValueAtTime({t0}, [0,0]); Sc{n}.setValueAtTime({t0 + 0.45:.3f}, [w{n},w{n}]);'
                  f' Ro{n}.setValueAtTime({t0}, {st["rot"] - 220}); Ro{n}.setValueAtTime({t0 + 0.45:.3f}, {st["rot"]});')
            else:
                a(f'Sc{n}.setValueAtTime({t0}, [w{n},w{n}]);')
                if kind == 'drop':
                    a(f'Po{n}.setValueAtTime({t0}, [{px:.1f},{py - 700:.1f}]); Po{n}.setValueAtTime({t0 + 0.28:.3f}, [{px:.1f},{py + 25:.1f}]);'
                      f' Po{n}.setValueAtTime({t0 + 0.42:.3f}, [{px:.1f},{py:.1f}]);')
                elif kind in ('slide_l', 'slide_r'):
                    x0 = -400 if kind == 'slide_l' else W + 400
                    a(f'Po{n}.setValueAtTime({t0}, [{x0},{py:.1f}]); Po{n}.setValueAtTime({t0 + 0.35:.3f}, [{px:.1f},{py:.1f}]);')
                elif kind == 'fade':
                    a(f'var Op{n} = P({v},"ADBE Opacity"); Op{n}.setValueAtTime({t0}, 0); Op{n}.setValueAtTime({t0 + 0.4:.3f}, 100);')
            # pop out at scene end (not after the last scene)
            if si < len(scenes) - 1:
                a(f'Sc{n}.setValueAtTime({end - 0.16:.3f}, [w{n},w{n}]); Sc{n}.setValueAtTime({end - 0.01:.3f}, [0,0]);')
            a(f'Ro{n}.expression = "value + Math.sin(time*2.2 + {n}) * 2.5";')
            a(f'var d{n} = {v}.Effects.addProperty("ADBE Drop Shadow"); d{n}.property("Distance").setValue(10); d{n}.property("Softness").setValue(22); d{n}.property("Opacity").setValue(55);')
            n += 1
    # --- captions (hand lettered, revealed left to right)
    for si, s in enumerate(scenes):
        end = min(dur, s['t'] + s['dur'])
        a(f'var c{si} = c.layers.addText({js(s["caption"])}); c{si}.inPoint = {s["t"]}; c{si}.outPoint = {round(end, 3)};')
        a(f'var cp{si} = c{si}.property("ADBE Text Properties").property("ADBE Text Document"); var cd{si} = cp{si}.value;')
        a(f'cd{si}.font = "CaveatBrush-Regular"; cd{si}.fontSize = 88; cd{si}.fillColor = [1,0.93,0.72]; cd{si}.applyStroke = true; cd{si}.strokeColor = [0.05,0.04,0.12];'
          f' cd{si}.strokeWidth = 6; cd{si}.justification = ParagraphJustification.CENTER_JUSTIFY; cp{si}.setValue(cd{si});')
        a(f'P(c{si},"ADBE Position").setValue([{W // 2}, {CAP_Y}]); P(c{si},"ADBE Rotate Z").setValue({-2 if si % 2 else 2});')
        if si > 0:
            a(f'var an{si} = c{si}.property("ADBE Text Properties").property("ADBE Text Animators").addProperty("ADBE Text Animator"); var ap{si} = an{si}.property("ADBE Text Animator Properties");')
            a(f'ap{si}.addProperty("ADBE Text Opacity").setValue(0); ap{si}.addProperty("ADBE Text Position 3D").setValue([0,40,0]);')
            a(f'var sl{si} = an{si}.property("ADBE Text Selectors").addProperty("ADBE Text Selector").property("ADBE Text Percent Start");')
            a(f'sl{si}.setValueAtTime({s["t"]}, 0); sl{si}.setValueAtTime({round(s["t"] + min(1.6, s["dur"] * 0.55), 3)}, 100);')
    # --- soft glow + handle
    a(f'var fx = c.layers.addSolid([0,0,0], "Glow", {W}, {H}, 1, {dur}); fx.adjustmentLayer = true;')
    a('var g = fx.Effects.addProperty("ADBE Glo2"); g.property("Glow Threshold").setValue(86); g.property("Glow Radius").setValue(45); g.property("Glow Intensity").setValue(0.6);')
    a('var h = c.layers.addText("@aitricksbysumit"); var hp = h.property("ADBE Text Properties").property("ADBE Text Document"); var hd = hp.value;')
    a('hd.font = "MontserratThin-Bold"; hd.fontSize = 30; hd.fillColor = [1,1,1]; hd.justification = ParagraphJustification.LEFT_JUSTIFY; hp.setValue(hd);')
    a('P(h,"ADBE Position").setValue([60, 400]);')
    a('"ok " + c.numLayers + " layers, " + c.duration + "s"')
    return '\n'.join(L)


if __name__ == '__main__':
    spec = json.load(open(sys.argv[1]))
    mx = float(sys.argv[4]) if len(sys.argv) > 4 else 1e9
    open(sys.argv[3], 'w').write(build(spec, sys.argv[2], mx))
    print('wrote', sys.argv[3])
