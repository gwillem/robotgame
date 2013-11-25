
# Bot coordination:

1. Calculate all proposals for all allies => yield proposals
2. Sort proposals on priority and deterministic algo => yield plan
3. Execute plan for self.location
4. Profit!

# Concepts:

swarm: surround enemy by at least 2 allies
safe_attack_spot: only bordering 1 enemy

is_static(bot) = bot hasn't moved last turn
is_vulnerable(bot) = bot has at least 2 safe_attack_spots

best_attack_spots = all vuln_enemy neighbours that have no other enemy neighbours 
best_attack_spots_now = best_attack_spots which can be occupied within 1 turn

assigned_enemies = all vulnerable enemies that have 2 allies nearby, 
                   and assigned a list of peers that are assigned
ally_assignments = a list of peers (not per se all) that have 1 enemy loc assigned

is_attackable(bot) = bot has  that can be occupied within 1 turn

# Individual bot strategy:

if spawn_imminent and i_am_at_spawn:
    try safe_flee
    try emergency_flee
    emergency_attack

elif nearby_enemies:
    if i_am_overwhelming_enemy: attack
    elif i_am_at_best_attack_spot: attack
    else:
        try safe_flee
        try forced_flee
        emergency_attack

else sort options to:
    500 move_away_from_spawn (if turn % 10 == 0)
    400 move_to_best_attack_spot
    200 preemptive strike
    100 try move_to_center_but_away_from_other_bots
     50 stand still


TODO

* if i did this last time, do minus 1
* detect if surrounded, then suicide

* pre-attack spawn points
* preemptive strike: attack square with most enemy moves likely
* remove items from plan where attack and move conflict

* add suicide
* swap places if somebody is under attack

* If last preemptive strike didn't yield result, don't repeat
* Run for your life if blocked at spawn point

* If enemy neighbour is surrounded by >1 ally, then attack. 
* If surrounded by enemies, flee to square with less enemies
* Only flee spawn point if turn % 10 == 0
* Flee: don't go to spawn point
* If a bot is locked AND at spawn point AND can't flee but also can't attack, then it 
  should run!
* self.adjacents is ugly
* If stuck at spawn, go to other spawn
* Only classify enemy as vulnerable, if he is static -> is_static()
* Optimize ally assignments (in assign_enemies()), as some bots now miss the boat

1. match replay keyboard shortcuts
3. match > display some more info about owners
4. disable -> remove bot

==

sys exit if you're about to loose
store match results in mongodb
