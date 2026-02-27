"""
Seed exercises and progressions for Calisthenics Tracker
Version 2: 2 Exercises, 7 Progressions each with Form Cues
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meinprojekt.settings')
django.setup()

from fitness.models import Exercise, Progression

# Delete existing data
Exercise.objects.all().delete()
Progression.objects.all().delete()

print("🎯 Seeding exercises and progressions...\n")

# ============= PUSH-UPS =============
push_ups = Exercise.objects.create(
    name='Push-ups',
    category='PUSH',
    description='Horizontal pushing exercise for chest, triceps, and shoulders',
    video_url='https://www.youtube.com/watch?v=IODxDxX7oi4',
    is_timed=False,
    order=1
)

push_progressions = [
    {
        'level': 1,
        'order': 1,
        'name': 'Wall Push-ups',
        'target_type': 'reps',
        'target_value': 8,
        'user_starts_here': False,
        'description': 'Stand ~1 meter from wall, hands at shoulder height. Lean toward wall with straight body, push back.',
        'form_cues': [
            '✓ Arms fully extended at top',
            '✓ Body stays straight (no hip bend)',
            '✓ Hold 1 second at top',
            '✓ 3 seconds controlled toward wall',
            '✓ Hands shoulder-width apart'
        ],
        'common_mistakes': [
            '❌ Pushing hips forward',
            '❌ Not fully extending arms',
            '❌ Moving too fast',
            '❌ Elbows flared out'
        ],
        'tips': 'Perfect for absolute beginners. Focus on movement pattern, not strength.'
    },
    {
        'level': 2,
        'order': 2,
        'name': 'Incline Push-ups',
        'target_type': 'reps',
        'target_value': 8,
        'user_starts_here': False,
        'description': 'Hands on elevated surface (table, chair). Body at angle, making it easier than standard.',
        'form_cues': [
            '✓ Higher hands = easier (adjust height)',
            '✓ Scapular protraction at top (push shoulder blades forward)',
            '✓ Elbows at 45° from body',
            '✓ Controlled descent (3 seconds)',
            '✓ Chest to surface'
        ],
        'common_mistakes': [
            '❌ Forgetting scapular protraction',
            '❌ Elbows too wide (90°)',
            '❌ Not going deep enough',
            '❌ Hips sagging'
        ],
        'tips': 'Start with high surface (table), gradually lower over weeks.'
    },
    {
        'level': 3,
        'order': 3,
        'name': 'Knee Push-ups',
        'target_type': 'reps',
        'target_value': 8,
        'user_starts_here': True,
        'description': 'On knees, hands shoulder-width. Chest nearly to floor, then push up. CRITICAL: Protract shoulder blades at top!',
        'form_cues': [
            '✓ SCAPULAR PROTRACTION at top (most important!)',
            '✓ Chest nearly touches floor (fist distance)',
            '✓ Elbows max 45° from body (NOT flared)',
            '✓ 3 seconds controlled descent',
            '✓ Body straight from knees to head (no sagging hips or butt in air)'
        ],
        'common_mistakes': [
            '❌ No scapular protraction at top (biggest mistake!)',
            '❌ Elbows flared too wide (90°)',
            '❌ Butt in the air',
            '❌ Hips sagging down',
            '❌ Not going deep enough'
        ],
        'tips': 'Most important progression for learning proper form. Master this before moving on!'
    },
    {
        'level': 4,
        'order': 4,
        'name': 'Standard Push-ups',
        'target_type': 'reps',
        'target_value': 8,
        'user_starts_here': False,
        'description': 'Classic push-up. Hands shoulder-width, body completely straight, chest to floor.',
        'form_cues': [
            '✓ Hands at torso level (not shoulder level) = more shoulder activation',
            '✓ Maximum scapular protraction at top',
            '✓ Chest nearly touches floor',
            '✓ Entire body tense (glutes, abs, legs)',
            '✓ 3 seconds controlled descent',
            '✓ Explosive push up (1 second)'
        ],
        'common_mistakes': [
            '❌ No protraction',
            '❌ Not going deep enough (half reps)',
            '❌ Hips sagging',
            '❌ Neck bent (look at floor)',
            '❌ Hands too wide'
        ],
        'tips': 'This is the "benchmark" push-up. Quality over quantity!'
    },
    {
        'level': 5,
        'order': 5,
        'name': 'Diamond Push-ups',
        'target_type': 'reps',
        'target_value': 6,
        'user_starts_here': False,
        'description': 'Hands close together forming diamond shape with index fingers and thumbs. Much harder on triceps.',
        'form_cues': [
            '✓ Hands form diamond (index fingers + thumbs touching)',
            '✓ Elbows stay close to body (very important)',
            '✓ Same protraction at top',
            '✓ Chest to hands',
            '✓ Slower tempo (harder)'
        ],
        'common_mistakes': [
            '❌ Elbows flaring out',
            '❌ Not going deep enough (this is hard!)',
            '❌ Rushing the movement',
            '❌ Losing protraction'
        ],
        'tips': 'Major triceps burner. Reduce target reps (6 instead of 8).'
    },
    {
        'level': 6,
        'order': 6,
        'name': 'Decline Push-ups',
        'target_type': 'reps',
        'target_value': 6,
        'user_starts_here': False,
        'description': 'Feet elevated on chair/box. More load on upper chest and shoulders. Harder than standard.',
        'form_cues': [
            '✓ More vertical load angle',
            '✓ Focus on upper chest',
            '✓ Same form cues as standard',
            '✓ Slow negative (3 seconds)',
            '✓ Full range of motion'
        ],
        'common_mistakes': [
            '❌ Feet too high (start low)',
            '❌ Losing form due to difficulty',
            '❌ Not maintaining body line'
        ],
        'tips': 'Bridges gap between standard and pike push-ups.'
    },
    {
        'level': 7,
        'order': 7,
        'name': 'Pseudo Planche Push-ups',
        'target_type': 'reps',
        'target_value': 5,
        'user_starts_here': False,
        'description': 'Hands at waist level, fingers outward 45°. Shoulders MUST be forward of hands. Advanced planche preparation.',
        'form_cues': [
            '✓ Hands at/behind waist level',
            '✓ Fingers 45° outward',
            '✓ Shoulders must be FORWARD of hands (lean forward heavily)',
            '✓ Maximum protraction',
            '✓ Very slow controlled movement',
            '✓ This should feel like planche position'
        ],
        'common_mistakes': [
            '❌ Hands too far forward (must be at waist)',
            '❌ Not leaning forward enough',
            '❌ Losing shoulder position',
            '❌ Rushing the movement'
        ],
        'tips': 'Advanced move. Significantly harder than standard. Direct planche preparation.'
    }
]

for prog in push_progressions:
    Progression.objects.create(
        exercise=push_ups,
        level=prog['level'],
        order=prog['order'],
        name=prog['name'],
        target_type=prog['target_type'],
        target_value=prog['target_value'],
        user_starts_here=prog['user_starts_here'],
        description=prog['description'],
        form_cues=prog['form_cues'],
        common_mistakes=prog['common_mistakes'],
        tips=prog['tips'],
        sets_required=2,
        sessions_required=3
    )
    print(f"✅ Created Push-ups progression: {prog['name']} (Level {prog['level']})")

# ============= PULL-UPS =============
pull_ups = Exercise.objects.create(
    name='Pull-ups',
    category='PULL',
    description='Vertical pulling exercise for back, biceps, and grip strength',
    video_url='https://www.youtube.com/watch?v=fO3dKSQayfg',
    is_timed=False,
    order=2
)

pull_progressions = [
    {
        'level': 1,
        'order': 1,
        'name': 'Dead Hang',
        'target_type': 'time',
        'target_value': 30,
        'user_starts_here': True,
        'description': 'Simply hang from bar. Arms fully extended, body relaxed. Builds grip strength foundation.',
        'form_cues': [
            '✓ Overhand grip (knuckles toward you)',
            '✓ Arms COMPLETELY extended (no bend)',
            '✓ Shoulders relaxed (let them hang up toward ears)',
            '✓ Feet cannot push off anything',
            '✓ Breathe calmly',
            '✓ Body hangs straight down'
        ],
        'common_mistakes': [
            '❌ Engaging shoulders (should be passive hang)',
            '❌ Swinging or kipping',
            '❌ Bent arms',
            '❌ Holding breath'
        ],
        'tips': 'Focus on grip endurance. When you can hold 30s easily, move to next progression.'
    },
    {
        'level': 2,
        'order': 2,
        'name': 'Scapular Shrugs',
        'target_type': 'reps',
        'target_value': 10,
        'user_starts_here': False,
        'description': 'Hang from bar and pull shoulder blades down and together. Builds scapular control - FOUNDATION for pull-ups!',
        'form_cues': [
            '✓ Start in dead hang',
            '✓ Pull shoulders DOWN and BACK (depression + retraction)',
            '✓ Body lifts slightly (1-2 inches)',
            '✓ Arms stay COMPLETELY straight (no arm bend!)',
            '✓ Slow and controlled (3 sec down, 1 sec up)',
            '✓ This is the FIRST movement in every pull-up'
        ],
        'common_mistakes': [
            '❌ Bending arms (this is not a pull-up!)',
            '❌ Moving too fast',
            '❌ Not getting full ROM',
            '❌ Swinging'
        ],
        'tips': 'Most important progression! Master this before negatives. Feel your back muscles working.'
    },
    {
        'level': 3,
        'order': 3,
        'name': 'Active Hang',
        'target_type': 'time',
        'target_value': 20,
        'user_starts_here': False,
        'description': 'Shoulders actively depressed (away from ears). Hold this engaged position. Builds scapular endurance.',
        'form_cues': [
            '✓ Shoulders DOWN (depression)',
            '✓ Back muscles engaged (you should feel lats)',
            '✓ Body slightly elevated vs dead hang (~1 inch)',
            '✓ Hold active position the entire time',
            '✓ Arms straight',
            '✓ This is "engaged" hang vs "dead" hang'
        ],
        'common_mistakes': [
            '❌ Relaxing shoulders (becomes dead hang)',
            '❌ Bending arms',
            '❌ Holding breath',
            '❌ Swinging'
        ],
        'tips': 'Builds endurance in the scapular depression. Every pull-up starts from here.'
    },
    {
        'level': 4,
        'order': 4,
        'name': 'Pull-up Negatives',
        'target_type': 'reps',
        'target_value': 5,
        'user_starts_here': False,
        'description': 'Jump or step to TOP position (chin over bar), then lower as slowly as possible. Directly builds pulling strength!',
        'form_cues': [
            '✓ Jump or step to TOP (chin over bar, elbows bent)',
            '✓ Lower as SLOW as possible (target: 5+ seconds)',
            '✓ Control entire descent',
            '✓ Full dead hang at bottom (arms straight)',
            '✓ Focus on the "braking" sensation',
            '✓ This builds eccentric strength = pull-up strength'
        ],
        'common_mistakes': [
            '❌ Dropping too fast (must be slow!)',
            '❌ Not starting from proper top position',
            '❌ Not going to full dead hang at bottom',
            '❌ Swinging or kipping',
            '❌ Giving up halfway down'
        ],
        'tips': 'THE most effective progression for building pull-up strength. 5+ seconds is the goal.'
    },
    {
        'level': 5,
        'order': 5,
        'name': 'Band-Assisted Pull-ups',
        'target_type': 'reps',
        'target_value': 8,
        'user_starts_here': False,
        'description': 'Full pull-ups with resistance band support. Use progressively thinner bands as you get stronger.',
        'form_cues': [
            '✓ Band under feet or knees (feet easier)',
            '✓ Full ROM (dead hang to chin over bar)',
            '✓ Don\'t rely too much on band momentum',
            '✓ Engage scapula first (depression)',
            '✓ Explosive up (1 sec), slow down (3 sec)',
            '✓ Chin must clear bar'
        ],
        'common_mistakes': [
            '❌ Using band as crutch (kick off it)',
            '❌ Not full ROM',
            '❌ Kipping/swinging',
            '❌ Rushing the movement'
        ],
        'tips': 'Start with thick band, progress to thinner. When you can do 8+ with thin band, try unassisted.'
    },
    {
        'level': 6,
        'order': 6,
        'name': 'Standard Pull-ups',
        'target_type': 'reps',
        'target_value': 5,
        'user_starts_here': False,
        'description': 'Full bodyweight pull-ups. THE GOAL for beginners! From dead hang to chin over bar.',
        'form_cues': [
            '✓ Dead hang start (arms completely straight)',
            '✓ Engage scapula FIRST (pull shoulders down)',
            '✓ Explosive pull up',
            '✓ Chin OVER bar (not just to bar)',
            '✓ Chest toward bar at top',
            '✓ 3 seconds controlled descent',
            '✓ No kipping/swinging (strict form)',
            '✓ Full dead hang at bottom (reset every rep)'
        ],
        'common_mistakes': [
            '❌ Half reps (not full ROM)',
            '❌ Kipping (using momentum)',
            '❌ Not engaging scapula first',
            '❌ Chin not over bar',
            '❌ Rushing the descent'
        ],
        'tips': 'The benchmark! When you can do 5 strict pull-ups, you are no longer a beginner.'
    },
    {
        'level': 7,
        'order': 7,
        'name': 'Chest-to-Bar Pull-ups',
        'target_type': 'reps',
        'target_value': 5,
        'user_starts_here': False,
        'description': 'Pull until chest touches bar, not just chin over. Much harder, full lat activation.',
        'form_cues': [
            '✓ Pull HIGHER than standard (chest to bar)',
            '✓ Explosive pull',
            '✓ Lean back slightly at top',
            '✓ Chest makes contact with bar',
            '✓ Full control on descent',
            '✓ Massive lat engagement'
        ],
        'common_mistakes': [
            '❌ Not pulling high enough',
            '❌ Using too much kip',
            '❌ Losing control',
            '❌ Not full ROM'
        ],
        'tips': 'Advanced progression. Requires significant strength. Gateway to muscle-ups.'
    }
]

for prog in pull_progressions:
    Progression.objects.create(
        exercise=pull_ups,
        level=prog['level'],
        order=prog['order'],
        name=prog['name'],
        target_type=prog['target_type'],
        target_value=prog['target_value'],
        user_starts_here=prog['user_starts_here'],
        description=prog['description'],
        form_cues=prog['form_cues'],
        common_mistakes=prog['common_mistakes'],
        tips=prog['tips'],
        sets_required=2,
        sessions_required=3
    )
    print(f"✅ Created Pull-ups progression: {prog['name']} (Level {prog['level']})")

print("\n✅ Seeding complete!")
print(f"  - {Exercise.objects.count()} exercises created")
print(f"  - {Progression.objects.count()} progressions created")
