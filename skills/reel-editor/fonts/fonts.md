# Title fonts

All fonts here are free Google Fonts under the SIL Open Font License (OFL), so they can be shared.
They are close lookalikes of popular travel and cinematic title lettering.

| Style (title_kit.py) | Reference look | Main font | Accent font |
|---|---|---|---|
| brush_grunge | KUMBHE: dry-brush caps with cracks | Permanent Marker + distress | |
| marker_stack | Wild Walker: rounded marker | Caveat Brush | |
| swash_serif | Typography (story): Victorian swash serif | Berkshire Swash | Montserrat 500 |
| bold_script | Spirit Birds: bold brush script | Kaushan Script | |
| circle_badge | Discover Tamil Nadu: script in a circle | Mr Dafoe + light distress | hand-drawn arcs |
| casual_script | Kerala Tales: heavy casual script | Leckerli One | |
| distressed_script | Spitiful: scratched elegant script | Parisienne + distress | |
| stacked_story | The Himachal Stories: stacked bouncy script | Dancing Script 700 + soft shadow | |
| western_grunge | Finding Maharashtra: retro western caps | Rye + distress | |
| classic_caps | LADAKH: Roman serif caps behind the subject | Cinzel 900 + shadow | |
| fast_brush | Langza: fast dry-brush script | Mr Dafoe + streaks | |
| swash_plus_tiny_script | Effects Typography | Berkshire Swash | Mrs Saint Delafield |
| kicker_serif | Take better Framing: pastel heavy serif | Abril Fatface (#F9EFA0) | Cinzel 700 kicker |
| brush_caps_badge | GOD'S MOUNTAIN: brush caps + spaced sans + icon | Permanent Marker (charcoal) | Montserrat 700, spaced |
| script_over_block | Gimbel MODES: thumbnail style | Anton yellow + hard black shadow | Sacramento |
| bubbly_fun | Life is a Highway | Chewy + sparkle strokes | |
| caps_signature | HEMKUND SAHIB Gurudwara | Montserrat 900 (#FFD64A) | Mrs Saint Delafield |
| calligraphy_kicker | Dhanushkodi, The last land | Great Vibes (cream #F6ECC8) | Montserrat 500 |
| spaced_caps_signature | JODHPUR Blue City | Montserrat 900, wide spacing, scene colour | Mrs Saint Delafield |
| script_word_kicker | Cinematic Adiyogi | Ruthie (yellow) | Montserrat 500 |

## Design rules learned from these titles

1. **One hero word + one tiny kicker.** A huge expressive word (script, brush or serif), plus a
   small clean sans or serif ("The last land", "Cinematic", "On story", "TAKE BETTER") tucked into
   the hero word's empty space, never floating far away.
2. **Script crosses caps.** A bold caps word (HEMKUND SAHIB, JODHPUR) with a thin signature script
   ("Gurudwara", "Blue City") overlapping its lower right corner.
3. **Texture matches the place.** Use grunge, cracks or dry-brush texture for mountains, forts,
   waterfalls and adventure. Use clean scripts for beaches, tea gardens and calm places.
4. **Colour comes from the scene.** Mostly white. Otherwise one accent picked from the photo:
   sky blue for Jodhpur, pastel yellow on a blue sky, cream on teal sea, yellow on a gold sunset,
   charcoal on a white cloudy sky.
5. **Stack and stagger.** Break a name into syllables or words on 2 to 4 lines
   (KUM/BHE, Hima/chal, MAHA/RASHTRA). Offset the lines slightly and tilt the whole block 3 to 6 degrees.
6. **Top third, subject below.** Keep the title above the subject. Use the depth trick when the
   subject is tall (text behind the head or peak, like LADAKH). Darken the top of the photo or add
   a soft shadow so white text stays readable.
7. **Decor is minimal.** At most one decoration: a hand-drawn circle, sparkle strokes, a mountain
   icon line, or a couple of doodles for a thumbnail.

# Hindi (Devanagari) title fonts (`scripts/deva_kit.py`)

All fonts in `fonts/deva/` are Google Fonts under the OFL. Pillow needs raqm for correct shaping
of matras and conjuncts.

| Style | Reference look | Font + effect |
|---|---|---|
| grunge_danger | संकटभाव, torn white on a dark photo | Yatra One + grunge |
| chalk | कलामयी, chalk on black | Kalam 700 + chalk texture |
| heavy_calligraphy | मृदुल / जीत, very heavy | Eczar 800 |
| rounded_mono | परिवर्तन / सृजन, rounded and friendly | Baloo 2 600/800 |
| sharp_hairline | नवोन्मेष, magenta with a diagonal hairline | Eczar 800 + hairline |
| thin_geometric_swash | गुलज़ार, thin line with a long left swash | Poppins 300 + bar + left swash |
| calligraphy_swash | भारत / रंगाम, bold calligraphy with a tail | Rozha One + swash |
| bold_hairline | अभिनंदन / विरासत, cream on red | Rozha One + hairline |
| mono_bar | उत्तराखंड, thin monoline with a long headline bar | Gotu + bar extension |
| rounded_swash | शब्दमाला | Baloo 2 + left swash + bar |
| flowing_calligraphy | मोक्षप्राप्ती / अदाएँ / श्रृंगार / नज़ाकत, pen calligraphy | Amita 700 + swash |
| flowing_light | अदाकारी | Amita 400 + bar |
| textured_heavy | हिन्दी with flower ornaments | Eczar 800 + grain + ornaments |
| jain_script | old manuscript look | Jaini Purva |
| latin_shirorekha | Mangalmay / Qasira / Chintaron, English dressed like Hindi | Akshar 700 Latin + top bar at x-height + swash |
| signature_outro | "Tha / IF YOU ENJOY MY CONTENT:" outro | Mrs Saint Delafield + spaced Montserrat caps |

## Rules from these designs

1. **Hindi hero word + English meaning.** One meaningful Hindi word (संकटभाव, परिवर्तन), with its English
   meaning in small letter-spaced caps (Montserrat 500, about 40 px) centred under it.
   This works well as a carousel or reel series: "Hindi words with beautiful meanings".
2. **The photo explains the word.** परिवर्तन sits on an orange, नवोन्मेष on a plasma ball, कलामयी on
   a pencil tip. White text on photos; on flat colour use cream #F6ECD6 with red #9B1A12 (either way round)
   or dark brown on parchment.
3. **Calligraphic flourishes carry the luxury feel.** Use a tapered swash tail from the last letter, a
   thin diagonal hairline through one letter, or a headline bar (shirorekha) running past the word.
   Use only one or two of these per word.
4. **Texture matches the meaning.** Grunge for danger, chalk for art, grain or wood for heritage,
   clean rounded strokes for soft and positive words.
5. **Paper grain.** Flat backgrounds get a fine grain or parchment pattern so they never look digital-flat.


# Lyric fonts (`scripts/phonetic_stretch.py`)

- `cormorant-garamond-700i.ttf`: Cormorant Garamond Bold Italic (OFL). Elegant calligraphic serif for qawwali, ghazal and Sufi lyrics, and it stays readable when vowels are stretched.
