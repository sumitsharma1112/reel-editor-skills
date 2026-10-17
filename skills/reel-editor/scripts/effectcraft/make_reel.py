"""make_reel.py — plan.json -> reel.jsx for EffectCraft (After Effects-style scripting object model).
1080x1920 comp: one image per beat-snapped shot with a scale punch; alternate cuts get a Linear Wipe;
white flash + blur pulse on every cut; cinematic Glow on an adjustment layer; per-word animated caption
(characters pop in through a text animator range selector); @handle.
usage: python3 make_reel.py plan.json assets_dir reel.jsx"""
import sys, json, os

W, H = 1080, 1920
OV = 0.2            # wipe overlap (s)


def js(v): return json.dumps(v, ensure_ascii=False)


def build(plan, assets):
    fps, dur = plan['fps'], plan['duration']
    L = []
    a = L.append
    a(f'var c = app.project.items.addComp("Reel", {W}, {H}, 1, {dur}, {fps});')
    a('function imp(p){ return app.project.importFile(new ImportOptions(new File(p))); }')
    a('function ease(prop, i){ var e=[new KeyframeEase(0,80)]; var d=prop.value.length?prop.value.length:1; var arr=[]; for(var k=0;k<(d>2?d:1);k++) arr.push(new KeyframeEase(0,80)); prop.setTemporalEaseAtKey(i, arr, arr); }')
    a('var song = imp(' + js(os.path.abspath(plan['song'])) + '); var aud = c.layers.add(song);')
    shots = plan['shots']
    # images: later shots above earlier ones
    for k, s in enumerate(shots):
        wipe = k > 0 and k % 2 == 0
        tin = max(0, s['start'] - (OV if wipe else 0))
        a(f'var f{k} = imp({js(os.path.join(os.path.abspath(assets), s["image"]))});')
        a(f'var l{k} = c.layers.add(f{k}); l{k}.inPoint = {tin}; l{k}.outPoint = {s["end"] + (OV if k + 1 < len(shots) and (k + 1) % 2 == 0 else 0)};')
        # cover-fit the still to 1080x1920, then punch 1.14 -> cover over 0.35 s and drift slowly
        a(f'var sc{k} = Math.max({W}/f{k}.width, {H}/f{k}.height)*100;')
        a(f'var S{k} = l{k}.property("ADBE Transform Group").property("ADBE Scale");')
        a(f'S{k}.setValueAtTime({s["start"]}, [sc{k}*1.14, sc{k}*1.14]); S{k}.setValueAtTime({s["start"] + 0.35}, [sc{k}*1.02, sc{k}*1.02]);'
          f' S{k}.setValueAtTime({s["end"]}, [sc{k}*1.06, sc{k}*1.06]);')
        if wipe:
            a(f'var w{k} = l{k}.Effects.addProperty("ADBE Linear Wipe"); var tc{k} = w{k}.property("Transition Completion");')
            a(f'tc{k}.setValueAtTime({tin}, 100); tc{k}.setValueAtTime({s["start"]}, 0);')
            a(f'w{k}.property("Wipe Angle").setValue({90 if k % 4 == 0 else 270}); w{k}.property("Feather").setValue(120);')
    # adjustment: glow + blur pulse on cuts
    a(f'var fx = c.layers.addSolid([0,0,0], "Cinematic FX", {W}, {H}, 1, {dur}); fx.adjustmentLayer = true;')
    a('var g = fx.Effects.addProperty("ADBE Glo2"); g.property("Glow Threshold").setValue(55); g.property("Glow Radius").setValue(70); g.property("Glow Intensity").setValue(0.9);')
    a('var bl = fx.Effects.addProperty("ADBE Gaussian Blur 2"); var br = bl.property("Blurriness");')
    a('br.setValueAtTime(0, 0);')
    for s in shots[1:]:
        t = s['start']
        a(f'br.setValueAtTime({round(t - 0.04, 3)}, 0); br.setValueAtTime({t}, 14); br.setValueAtTime({round(t + 0.12, 3)}, 0);')
    # white flash on cuts
    a(f'var fl = c.layers.addSolid([1,1,1], "Flash", {W}, {H}, 1, {dur}); var fo = fl.property("ADBE Transform Group").property("ADBE Opacity");')
    a('fo.setValueAtTime(0, 0);')
    for s in shots[1:]:
        t = s['start']
        a(f'fo.setValueAtTime({round(t - 1 / fps, 4)}, 0); fo.setValueAtTime({t}, 55); fo.setValueAtTime({round(t + 0.15, 3)}, 0);')
    # captions: one text layer per word, characters pop in via an animator + range selector
    for k, s in enumerate(shots):
        if not s['word']: continue
        a(f'var t{k} = c.layers.addText({js(s["word"])}); t{k}.inPoint = {s["start"]}; t{k}.outPoint = {s["end"]};')
        a(f'var sp{k} = t{k}.property("ADBE Text Properties").property("ADBE Text Document"); var d{k} = sp{k}.value;')
        a(f'd{k}.font = "Baloo2-ExtraBold"; d{k}.fontSize = 110; d{k}.fillColor = [1, 0.84, 0.47]; d{k}.applyStroke = true;'
          f' d{k}.strokeColor = [0.12,0.03,0]; d{k}.strokeWidth = 8; d{k}.justification = ParagraphJustification.CENTER_JUSTIFY; sp{k}.setValue(d{k});')
        a(f't{k}.property("ADBE Transform Group").property("ADBE Position").setValue([{W // 2}, 1180]);')
        a(f'var an{k} = t{k}.property("ADBE Text Properties").property("ADBE Text Animators").addProperty("ADBE Text Animator");')
        a(f'var ap{k} = an{k}.property("ADBE Text Animator Properties");')
        a(f'ap{k}.addProperty("ADBE Text Opacity").setValue(0); ap{k}.addProperty("ADBE Text Scale 3D").setValue([180,180,100]);')
        a(f'var sel{k} = an{k}.property("ADBE Text Selectors").addProperty("ADBE Text Selector"); var st{k} = sel{k}.property("ADBE Text Percent Start");')
        if k == 0: a(f'st{k}.setValue(100);')                     # hook: first word fully visible on frame 0
        else: a(f'st{k}.setValueAtTime({s["start"]}, 0); st{k}.setValueAtTime({round(s["start"] + 0.3, 3)}, 100);')
    a('var h = c.layers.addText("@aitricksbysumit"); var hp = h.property("ADBE Text Properties").property("ADBE Text Document"); var hd = hp.value;')
    a('hd.font = "MontserratThin-Bold"; hd.fontSize = 30; hd.fillColor = [1,1,1]; hd.justification = ParagraphJustification.LEFT_JUSTIFY; hp.setValue(hd);')
    a('h.property("ADBE Transform Group").property("ADBE Position").setValue([56, 480]);')
    a('"ok " + c.numLayers + " layers"')
    return '\n'.join(L)


if __name__ == '__main__':
    plan = json.load(open(sys.argv[1]))
    open(sys.argv[3], 'w').write(build(plan, sys.argv[2]))
    print('wrote', sys.argv[3])
