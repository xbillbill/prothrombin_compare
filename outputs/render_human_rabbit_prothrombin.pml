# Publication-oriented PyMOL render script for human vs rabbit prothrombin.
# Run from project root:
#   pymol -cq outputs/render_human_rabbit_prothrombin.pml
reinitialize
set ray_opaque_background, off
set antialias, 2
set cartoon_fancy_helices, 1
set sphere_scale, 0.45
bg_color white
load /Users/billwang/alphafold/prothrombin_compare/data/structures/human_AF_P00734.pdb, human
load /Users/billwang/alphafold/prothrombin_compare/data/structures/rabbit_aligned_to_human.pdb, rabbit

hide everything
show cartoon, human
color gray70, human
select human_first_Xa_window, human and resi 300-330
select human_first_Xa_site, human and resi 314+315
select human_second_Xa_window, human and resi 350-375
select human_second_Xa_site, human and resi 363+364
select human_deletion_segment, human and resi 299+300+301+302+303
select human_thrombin_domain, human and resi 364-622
color red, human_first_Xa_window
color orange, human_second_Xa_window
color magenta, human_deletion_segment
color blue, human_thrombin_domain
show sticks, human_first_Xa_site or human_second_Xa_site or human_deletion_segment
show spheres, human_first_Xa_site or human_second_Xa_site

show cartoon, rabbit
color cyan, rabbit
select rabbit_first_Xa_region, rabbit and resi 300+301+302+303+304+305+306+307+308+309+310+311+312+313+314+315+316+317+318+319+320+321+322+323+324+325+326
select rabbit_second_Xa_region, rabbit and resi 346+347+348+349+350+351+352+353+354+355+356+357+358+359+360+361+362+363+364+365+366+367+368+369+370+371
select rabbit_deletion_flanks, rabbit and resi 296+297+298+299+300+301+302+303
color cyan, rabbit_first_Xa_region
color marine, rabbit_second_Xa_region
color magenta, rabbit_deletion_flanks
show sticks, rabbit_first_Xa_region or rabbit_second_Xa_region or rabbit_deletion_flanks

set_view (     0.913,   -0.277,    0.299,     0.242,    0.958,    0.153,    -0.329,   -0.067,    0.942,     0.000,    0.000, -260.000,   315.000,  310.000,  305.000,   190.000,  320.000,  -20.000 )

# 01 whole protein overlay
orient human
zoom human, 12
png outputs/renderings/01_whole_overlay.png, width=1800, height=1400, ray=1

# 02 first factor Xa cleavage region
orient human_first_Xa_window
zoom human_first_Xa_window, 12
png outputs/renderings/02_first_xa_closeup.png, width=1800, height=1400, ray=1

# 03 human deletion segment and rabbit flanking residues
orient human_deletion_segment or rabbit_deletion_flanks
zoom human_deletion_segment or rabbit_deletion_flanks, 10
png outputs/renderings/03_deletion_flanks.png, width=1800, height=1400, ray=1

# 04 second factor Xa site as a control region
orient human_second_Xa_window
zoom human_second_Xa_window, 12
png outputs/renderings/04_second_xa_control.png, width=1800, height=1400, ray=1

# 05 first Xa surface context
show surface, human_first_Xa_window
set transparency, 0.45, human_first_Xa_window
orient human_first_Xa_window
zoom human_first_Xa_window, 14
png outputs/renderings/05_first_xa_surface.png, width=1800, height=1400, ray=1
hide surface

save outputs/prothrombin_compare.pse
