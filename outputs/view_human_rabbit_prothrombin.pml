# PyMOL visualization for human vs rabbit prothrombin.
# Run from project root: pymol outputs/view_human_rabbit_prothrombin.pml
reinitialize
load /Users/billwang/alphafold/prothrombin_compare/data/structures/human_AF_P00734.pdb, human
load /Users/billwang/alphafold/prothrombin_compare/data/structures/rabbit_aligned_to_human.pdb, rabbit

hide everything
show cartoon, human
color gray70, human
select human_first_Xa_site, human and resi 314+315
select human_second_Xa_site, human and resi 363+364
select human_first_Xa_window, human and resi 300-330
select human_second_Xa_window, human and resi 350-375
select human_thrombin_domain, human and resi 364-622
select human_kringle_regions, human and resi 103-183+203-283
color red, human_first_Xa_window
color orange, human_second_Xa_window
color blue, human_thrombin_domain
color yellow, human_kringle_regions
show sticks, human_first_Xa_site or human_second_Xa_site
show spheres, human_first_Xa_site or human_second_Xa_site

show cartoon, rabbit
color cyan, rabbit
select rabbit_first_Xa_region, rabbit and resi 300+301+302+303+304+305+306+307+308+309+310+311+312+313+314+315+316+317+318+319+320+321+322+323+324+325+326
select rabbit_deletion_region, rabbit and resi 297+298+299+300+301+302
color magenta, rabbit_deletion_region
show sticks, rabbit_first_Xa_region or rabbit_deletion_region

bg_color white
set cartoon_fancy_helices, 1
set ray_opaque_background, off
orient human_first_Xa_window
zoom human_first_Xa_window, 18
save outputs/prothrombin_compare.pse
