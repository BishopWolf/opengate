import pathlib
from opengate.geometry.volumes import unite_volumes
from opengate.geometry.volumes import RepeatParametrisedVolume, BoxVolume
from opengate.actors.digitizers import *
from opengate.managers import Simulation
from opengate.utility import g4_units
from opengate.contrib.spect.spect_helpers import (
    get_volume_position_in_head,
    get_default_energy_windows,
)
from opengate.geometry.utility import get_transform_orbiting

# colors
# red = [1, 0.7, 0.7, 0.8]
# blue = [0.5, 0.5, 1, 0.8]
# gray = [0.5, 0.5, 0.5, 1]
# white = [1, 1, 1, 1]
# yellow = [1, 1, 0, 1]
# green = [0, 1, 0, 1]


def add_spect_head(sim, name="spect", collimator_type="lehr", debug=False):
    """
    Collimator:
    - False or "none" : no collimator
    - LEHR  : 1.11 mm holes
    - MELP  : 2.94 mm holes
    - HE    : 4 mm holes

    Collimator LEHR: Low Energy High Resolution    (for Tc99m)
    Collimator MELP: Medium Energy Low Penetration (for In111, Lu177)
    Collimator HE:   High Energy General Purpose   (for I131)

    """
    f = pathlib.Path(__file__).parent.resolve()
    fdb = f"{f}/spect_siemens_intevo_materials.db"
    if fdb not in sim.volume_manager.material_database.filenames:
        sim.volume_manager.add_material_database(fdb)

    # check overlap
    sim.check_volumes_overlap = debug

    # main box
    head = add_head_box(sim, name)

    # shielding (important)
    add_shielding(sim, head, collimator_type)

    # collimator
    colli = add_collimator(sim, head, collimator_type, debug)

    # crystal
    crystal = add_crystal(sim, head)

    # other elements
    back_comp = add_back_compartment(sim, head)
    light_guide = add_light_guide(sim, back_comp)
    # pmt = add_PMT_array(sim, head)
    # elec = add_electronics(sim, head)

    return head, colli, crystal


def add_head_box(sim, name):
    mm = g4_units.mm
    # bounding box
    head = sim.add_volume("Box", name)
    head.material = "G4_AIR"
    head.size = [260.0448 * mm, 685 * mm, 539 * mm]
    white = [1, 1, 1, 1]
    head.color = white
    return head


def add_shielding(sim, head, collimator_type):
    if collimator_type == "lehr" or collimator_type == "melp":
        return add_shielding_lehr_melp(sim, head)
    if collimator_type == "he":
        return add_shielding_he(sim, head)


def add_shielding_lehr_melp(sim, head):
    mm = g4_units.mm
    # shielding side thickness
    side_thickness = 12.7 * mm
    front_depth = 60 * mm
    side_depth = 215.0448 * mm - front_depth
    name = head.name

    # shielding
    back_shield = BoxVolume(name=f"{name}_back_shield")
    back_shield.size = [17.1 * mm, head.size[1], head.size[2]]

    # side shield Y pos
    side_shield_y_pos = BoxVolume(name=f"{name}_side_shield_y_pos")
    side_shield_y_pos.size = [side_depth, side_thickness, head.size[2]]

    # side shield Z pos
    side_shield_z_pos = BoxVolume(name=f"{name}_side_shield_z_pos")
    # gate.geometry.utility.copy_volume_user_info(side_shield_y_pos, side_shield_z_pos)
    side_shield_z_pos.size = [side_depth, head.size[1], side_thickness]

    # first volume from the 5 solids
    dx = -98.9724 * mm
    ddx = dx + front_depth / 2
    a = unite_volumes(back_shield, side_shield_y_pos, [ddx, 336.15 * mm, 0])
    a = unite_volumes(a, side_shield_y_pos, [ddx, -336.15 * mm, 0])
    a = unite_volumes(a, side_shield_z_pos, [ddx, 0, 263.15 * mm])
    shield = unite_volumes(
        a,
        side_shield_z_pos,
        [ddx, 0, -263.15 * mm],
        new_name=f"{name}_shielding_back_side",
    )
    sim.add_volume(shield)
    shield.mother = head.name
    shield.translation = [-dx, 0, 0]
    gray = [0.5, 0.5, 0.5, 1]
    shield.color = gray
    shield.material = "Lead"

    # front shields
    front_shield_y_pos = BoxVolume(name=f"{name}_front_shield_y_pos")
    front_shield_y_pos.size = [front_depth, 76 * mm, 510.4 * mm]
    front_shield_z_pos = BoxVolume(name=f"{name}_front_shield_z_pos")
    front_shield_z_pos.size = [front_depth, 676.7 * mm, 76 * mm]

    # second volume from the 4 solids
    a = front_shield_y_pos
    t = 304.5 * mm
    a = unite_volumes(a, front_shield_y_pos, [0, -2 * t, 0])
    a = unite_volumes(a, front_shield_z_pos, [0, -t, 231.5 * mm])
    shield = unite_volumes(
        a, front_shield_z_pos, [0, -t, -231.5 * mm], new_name=f"{name}_shielding_front"
    )
    sim.add_volume(shield)
    shield.mother = head.name
    shield.translation = [-87.0776 * mm, t, 0]
    shield.color = gray
    shield.material = "Lead"

    return shield


def add_shielding_he(sim, head):
    mm = g4_units.mm
    # shielding side thickness
    side_thickness = 12.7 * mm
    front_depth = 60 * mm
    side_depth = 215.0448 * mm - front_depth
    name = head.name

    # shielding
    back_shield = BoxVolume(name=f"{name}_back_shield")
    back_shield.size = [17.1 * mm, head.size[1], head.size[2]]

    # side shield Y pos
    side_shield_y_pos = BoxVolume(name=f"{name}_side_shield_y_pos")
    side_shield_y_pos.size = [side_depth, side_thickness, head.size[2]]

    # side shield Z pos
    side_shield_z_pos = BoxVolume(name=f"{name}_side_shield_z_pos")
    # gate.geometry.utility.copy_volume_user_info(side_shield_y_pos, side_shield_z_pos)
    side_shield_z_pos.size = [side_depth, head.size[1], side_thickness]

    # first volume from the 5 solids
    dx = -98.9724 * mm
    ddx = dx + front_depth / 2
    a = unite_volumes(back_shield, side_shield_y_pos, [ddx, 336.15 * mm, 0])
    a = unite_volumes(a, side_shield_y_pos, [ddx, -336.15 * mm, 0])
    a = unite_volumes(a, side_shield_z_pos, [ddx, 0, 263.15 * mm])
    shield = unite_volumes(
        a,
        side_shield_z_pos,
        [ddx, 0, -263.15 * mm],
        new_name=f"{name}_shielding_back_side",
    )
    sim.add_volume(shield)
    shield.mother = head.name
    shield.translation = [-dx, 0, 0]
    gray = [0.5, 0.5, 0.5, 1]
    shield.color = gray
    shield.material = "Lead"

    # front shields
    ofy = 35 * mm
    ofz = 30 * mm
    front_shield_y_pos = BoxVolume(name=f"{name}_front_shield_y_pos")
    front_shield_y_pos.size = [front_depth, 76 * mm - ofy, 510.4 * mm]
    front_shield_z_pos = BoxVolume(name=f"{name}_front_shield_z_pos")
    front_shield_z_pos.size = [front_depth, 676.7 * mm, 76 * mm - ofz]

    # second volume from the 4 solids
    a = front_shield_y_pos
    ty = 304.5 * mm + ofy / 2
    tz = 231.5 * mm + ofz / 2
    a = unite_volumes(a, front_shield_y_pos, [0, -2 * ty, 0])
    a = unite_volumes(a, front_shield_z_pos, [0, -ty, tz])
    shield = unite_volumes(
        a, front_shield_z_pos, [0, -ty, -tz], new_name=f"{name}_shielding_front"
    )
    sim.add_volume(shield)
    shield.mother = head.name
    shield.translation = [-87.0776 * mm, ty, 0]
    blue = [0.5, 0.5, 1, 0.8]
    shield.color = blue
    shield.material = "Lead"

    return shield


def add_collimator(sim, head, collimator_type, debug):
    if (
        collimator_type is False
        or collimator_type is None
        or collimator_type == ""
        or collimator_type == "none"
    ):
        return add_collimator_empty(sim, head)
    collimator_type = collimator_type.lower()
    if collimator_type == "lehr":
        return add_collimator_lehr(sim, head, debug)
    if collimator_type == "melp":
        return add_collimator_melp(sim, head, debug)
    if collimator_type == "he":
        return add_collimator_he(sim, head, debug)
    col = ["None", "lehr", "melp", "he"]
    fatal(
        f'Cannot build the collimator "{collimator_type}". '
        f"Available collimator types are: {col}"
    )
    return None


def add_collimator_empty(sim, head):
    mm = g4_units.mm
    colli = sim.add_volume("Box", f"{head.name}_no_collimator")
    colli.mother = head.name
    colli.size = [59.7 * mm, 533 * mm, 387 * mm]
    colli.translation = [-96.7324 * mm, 0, 0]
    blue = [0.5, 0.5, 1, 0.8]
    colli.color = blue
    colli.material = head.material
    return colli


def add_collimator_lehr(sim, head, debug):
    mm = g4_units.mm
    name = head.name
    colli = sim.add_volume("Box", f"{name}_collimator")
    colli.mother = name
    colli.size = [24.05 * mm, 533 * mm, 387 * mm]
    colli.translation = [-78.9074 * mm, 0, 0]
    blue = [0.5, 0.5, 1, 0.8]
    colli.color = blue
    colli.material = "Lead"

    """
    #########################################################################
    #
    # 	Type	|	Diameter	|	Septal thickness	|	No. of holes
    # -----------------------------------------------------------------------
    # 	hex		|	1.11 mm		|	0.16 mm 			|	148000
    #
    #	y spacing	= diameter + septal = 1.27 mm
    #	z spacing	= 2 * (diameter + septal) * sin(60) = 2.19970453 mm
    #
    #	y translation	= y spacing / 2 = 0.635 mm
    #	z translation	= z spacing / 2 = 1.09985 mm
    #
    # 	(this translation from 0,0 is split between hole1 and hole2)
    #
    #	Nholes y	= (No. of holes / sin(60))^0.5 = 413.4
    #	Nholes z	= (No. of holes * sin(60))^0.5 = 358
    #
    #########################################################################
    """

    # hexagon
    hole = sim.add_volume("Hexagon", f"{name}_collimator_hole1")
    hole.height = 24.05 * mm
    hole.radius = 0.555 * mm
    hole.material = "G4_AIR"
    hole.mother = colli.name

    # parameterised holes
    size = [1, 414, 175]
    if debug:
        size = [1, 30, 20]
    tr = [0, 1.27 * mm, 2.1997 * mm, 0]
    rot = Rotation.from_euler("y", 90, degrees=True).as_matrix()
    offset = [0, 0.3175 * mm * 2, 0.549925 * mm * 2, 0]
    repeat_colli_hole(sim, hole, size, tr, rot, offset)

    return colli


def add_collimator_melp(sim, head, debug):
    name = head.name
    mm = g4_units.mm

    colli = sim.add_volume("Box", f"{name}_collimator")
    colli.mother = name
    colli.size = [40.64 * mm, 533 * mm, 387 * mm]
    colli.translation = [-87.2024 * mm, 0, 0]
    blue = [0.5, 0.5, 1, 0.8]
    colli.color = blue
    colli.material = "Lead"

    """
    #########################################################################
    #
    # 	Type	|	Diameter	|	Septal thickness	|	No. of holes
    # -----------------------------------------------------------------------
    # 	hex		|	2.94 mm		|	1.14 mm 			|	14000
    #
    #	y spacing	= diameter + septal = 4.08 mm
    #	z spacing	= 2 * (diameter + septal) * sin(60) = 7.06676729 mm
    #
    #	y translation	= y spacing / 2 = 2.04 mm
    #	z translation	= z spacing / 2 = 3.53338 mm
    #
    # 	(this translation from 0,0 is split between hole1 and hole2)
    #
    #	Nholes y	= (No. of holes / sin(60))^0.5 = 127.1448
    #	Nholes z	= (No. of holes * sin(60))^0.5 = 110.111
    #
    #########################################################################
    """

    # hexagon
    hole = sim.add_volume("Hexagon", f"{name}_collimator_hole1")
    hole.height = 40.64 * mm
    hole.radius = 1.47 * mm
    hole.material = "G4_AIR"
    hole.mother = colli.name
    hole.build_physical_volume = False  # FIXME remove
    hole.color = [1, 0, 0, 1]

    # parameterised holes
    size = [1, 128, 55]
    if debug:
        size = [1, 30, 20]
    tr = [0, 4.08 * mm, 7.066767 * mm, 0]
    rot = Rotation.from_euler("y", 90, degrees=True).as_matrix()
    offset = [0, 1.02 * mm * 2, 1.76669 * mm * 2, 0]
    repeat_colli_hole(sim, hole, size, tr, rot, offset)

    return colli


def repeat_colli_hole(sim, hole, size, tr, rot, offset):
    holep = RepeatParametrisedVolume(repeated_volume=hole)
    holep.linear_repeat = size
    holep.translation = tr[0:3]
    holep.rotation = rot
    holep.start = [-(x - 1) * y / 2.0 for x, y in zip(size, tr)]
    # do it twice, with the following offset
    holep.offset_nb = 2
    holep.offset = offset
    sim.volume_manager.add_volume(holep)
    return holep


def add_collimator_he(sim, head, debug):
    name = head.name
    mm = g4_units.mm

    """gate.fatal(
        f"the Intevo HE collimator is not implemented yet. Need to move the shielding ..."
    )"""

    colli = sim.add_volume("Box", f"{name}_collimator")
    colli.mother = name
    colli.size = [59.7 * mm, 583 * mm, 440 * mm]
    colli.translation = [-96.7324 * mm, 0, 0]
    blue = [0.5, 0.5, 1, 0.8]
    colli.color = blue
    colli.material = "Lead"

    """
    #########################################################################
    #
    # 	Type	|	Diameter	|	Septal thickness	|	No. of holes
    # -----------------------------------------------------------------------
    # 	hex		|	4.0 mm		|	2.0 mm 				|	8000
    #
    #	y spacing	= diameter + Septal = 6.0 mm
    #	z spacing	= 2 * (diameter + Septal) * sin(60) = 10.39230485 mm
    #
    #	y translation	= y spacing / 2 = 3.0 mm
    #	z translation	= z spacing / 2 = 5.196152423 mm
    #
    # 	(this translation from 0,0 is split between hole1 and hole2)
    #
    #	Nholes y	= (No. of holes / sin(60))^0.5 = 96.11245657
    #	Nholes z	= (No. of holes * sin(60))^0.5 = 83.23582901
    #
    #########################################################################
    """

    # hexagon
    hole = sim.add_volume("Hexagon", f"{name}_collimator_hole1")
    hole.height = 59.7 * mm
    hole.radius = 2.0 * mm
    hole.material = "G4_AIR"
    hole.mother = colli.name

    # parameterised holes
    size = [1, 96, 42]
    if debug:
        size = [1, 30, 20]
    tr = [0, 6 * mm, 10.39230485 * mm, 0]
    rot = Rotation.from_euler("y", 90, degrees=True).as_matrix()
    offset = [0, -1.5 * mm * 2, -2.598076212 * mm * 2, 0]
    repeat_colli_hole(sim, hole, size, tr, rot, offset)

    return colli


def add_crystal(sim, head):
    mm = g4_units.mm
    front_shield_size = 76 * mm * 2
    red = [1, 0.0, 0.0, 0.9]

    name = head.name
    crystal_sheath = sim.add_volume("Box", f"{name}_crys_sheath")
    crystal_sheath.mother = name
    crystal_sheath.size = [
        0.3048 * mm,  # , 591 * mm, 445 * mm
        head.size[1] - front_shield_size,
        head.size[2] - front_shield_size,
    ]
    crystal_sheath.translation = [-66.73 * mm, 0, 0]
    crystal_sheath.material = "Aluminium"
    crystal_sheath.color = red

    crystal = sim.add_volume("Box", f"{name}_crystal")
    crystal.mother = name
    crystal.size = [
        9.5 * mm,  # , 591 * mm, 445 * mm
        head.size[1] - front_shield_size,
        head.size[2] - front_shield_size,
    ]
    # print(crystal.size) # [533 * mm, 387 * mm]

    crystal.translation = [-61.8276 * mm, 0, 0]
    crystal.material = "NaI"
    crystal.color = red

    return crystal


def add_back_compartment(sim, head):
    mm = g4_units.mm
    name = head.name
    back_compartment = sim.add_volume("Box", f"{name}_back_compartment")
    back_compartment.mother = name
    back_compartment.size = [147.5 * mm, 651.0 * mm, 485.0 * mm]
    back_compartment.translation = [16.6724 * mm, 0, 0]
    back_compartment.material = "G4_AIR"  # FIXME strange ?
    green = [0, 1, 0, 1]
    back_compartment.color = green
    return back_compartment


def add_light_guide(sim, back_compartment):
    mm = g4_units.mm
    name = back_compartment.name
    light_guide = sim.add_volume("Box", f"{name}_light_guide")
    light_guide.mother = name
    light_guide.size = [9.5 * mm, 643.0 * mm, 477.1037366 * mm]
    light_guide.translation = [-69.0 * mm, 0, 0]
    light_guide.material = "Glass"
    green = [0, 1, 0, 1]
    light_guide.color = green

    return light_guide


def add_digitizer_lu177(sim, crystal_name, name):
    # create main chain
    mm = g4_units.mm
    digitizer = Digitizer(sim, crystal_name, name)

    # Singles
    sc = digitizer.add_module("DigitizerAdderActor", f"{name}_singles")
    sc.group_volume = None
    sc.policy = "EnergyWinnerPosition"

    # detection efficiency
    ea = digitizer.add_module("DigitizerEfficiencyActor")
    ea.efficiency = 0.86481

    # energy blurring
    keV = g4_units.keV
    eb = digitizer.add_module("DigitizerBlurringActor")
    eb.blur_attribute = "TotalEnergyDeposit"
    eb.blur_method = "InverseSquare"
    eb.blur_resolution = 0.0945
    eb.blur_reference_value = 140.57 * keV
    # eb.blur_resolution = 0.13
    # eb.blur_reference_value = 80 * keV
    # eb.blur_slope = -0.09 * 1 / MeV  # fixme unsure about unit

    # spatial blurring
    # Source: HE4SPECS - FWHM = 3.9 mm
    # FWHM = 2.sigma.sqrt(2ln2) -> sigma = 1.656 mm
    sb = digitizer.add_module("DigitizerSpatialBlurringActor")
    sb.blur_attribute = "PostPosition"
    sb.blur_fwhm = 3.9 * mm
    sb.keep_in_solid_limits = True
    sb.use_truncated_Gaussian = False

    # energy windows (Energy range. 35-588 keV)
    cc = digitizer.add_module("DigitizerEnergyWindowsActor", f"{name}_energy_window")
    keV = g4_units.keV
    # 112.9498 keV  = 6.20 %
    # 208.3662 keV  = 10.38 %
    p1 = 112.9498 * keV
    p2 = 208.3662 * keV
    channels = [
        *energy_windows_peak_scatter("peak113", "scatter1", "scatter2", p1, 0.2, 0.1),
        *energy_windows_peak_scatter("peak208", "scatter3", "scatter4", p2, 0.2, 0.1),
    ]
    cc.channels = channels

    # projection
    proj = digitizer.add_module("DigitizerProjectionActor", f"{name}_projection")
    channel_names = [c["name"] for c in channels]
    proj.input_digi_collections = channel_names
    proj.spacing = [4.7951998710632 * mm / 2, 4.7951998710632 * mm / 2]
    proj.size = [256, 256]
    # by default, the origin of the images are centered
    # set to False here to keep compatible with previous version
    # proj.origin_as_image_center = False
    # projection plane: it depends on how the spect device is described
    # here, we need this rotation
    proj.detector_orientation_matrix = Rotation.from_euler(
        "yx", (90, 90), degrees=True
    ).as_matrix()

    # end
    return digitizer


def add_digitizer_tc99m(sim, crystal_name, name):
    # create main chain
    mm = g4_units.mm
    digitizer = Digitizer(sim, crystal_name, name)

    # Singles
    sc = digitizer.add_module("DigitizerAdderActor", f"{name}_singles")
    sc.group_volume = None
    sc.policy = "EnergyWinnerPosition"

    # detection efficiency
    ea = digitizer.add_module("DigitizerEfficiencyActor")
    ea.efficiency = 0.86481  # FAKE

    # energy blurring
    keV = g4_units.keV
    eb = digitizer.add_module("DigitizerBlurringActor")
    eb.blur_attribute = "TotalEnergyDeposit"
    eb.blur_method = "InverseSquare"
    eb.blur_resolution = 0.0945
    eb.blur_reference_value = 140.57 * keV

    # spatial blurring
    # Source: HE4SPECS - FWHM = 3.9 mm
    # FWHM = 2.sigma.sqrt(2ln2) -> sigma = 1.656 mm
    sb = digitizer.add_module("DigitizerSpatialBlurringActor")
    sb.blur_attribute = "PostPosition"
    # intrinsic spatial resolution at 140 keV for 9.5 mm thick NaI
    sb.blur_fwhm = 3.9 * mm
    sb.keep_in_solid_limits = True
    sb.use_truncated_Gaussian = False

    # energy windows (Energy range. 35-588 keV)
    cc = digitizer.add_module("DigitizerEnergyWindowsActor", f"{name}_energy_window")
    channels = [
        {"name": f"scatter", "min": 108.57749938965 * keV, "max": 129.5924987793 * keV},
        {"name": f"peak140", "min": 129.5924987793 * keV, "max": 150.60751342773 * keV},
    ]
    cc.channels = channels

    # projection
    proj = digitizer.add_module("DigitizerProjectionActor", f"{name}_projection")
    channel_names = [c["name"] for c in channels]
    proj.input_digi_collections = channel_names
    proj.spacing = [4.7951998710632 * mm / 2, 4.7951998710632 * mm / 2]
    proj.size = [256, 256]
    # by default, the origin of the images are centered
    # set to False here to keep compatible with previous version
    # proj.origin_as_image_center = False
    # projection plane: it depends on how the spect device is described
    # here, we need this rotation
    proj.detector_orientation_matrix = Rotation.from_euler(
        "yx", (90, 90), degrees=True
    ).as_matrix()
    # proj.output_filename = "proj.mhd"

    # end
    return digitizer


def add_digitizer_tc99m_v2(sim, crystal_name, name, spectrum_channel=True):
    # create main chain
    mm = g4_units.mm
    digitizer = Digitizer(sim, crystal_name, name)

    # Singles
    sc = digitizer.add_module("DigitizerAdderActor", f"{name}_singles")
    sc.group_volume = None
    sc.policy = "EnergyWinnerPosition"

    # detection efficiency
    # ea = digitizer.add_module("DigitizerEfficiencyActor")
    # ea.efficiency = 0.86481  # FAKE

    # energy blurring
    keV = g4_units.keV
    eb = digitizer.add_module("DigitizerBlurringActor")
    eb.blur_attribute = "TotalEnergyDeposit"
    eb.blur_method = "InverseSquare"
    eb.blur_resolution = 0.0945
    eb.blur_reference_value = 140.57 * keV

    # spatial blurring
    # Source: HE4SPECS - FWHM = 3.9 mm
    # FWHM = 2.sigma.sqrt(2ln2) -> sigma = 1.656 mm
    sb = digitizer.add_module("DigitizerSpatialBlurringActor")
    sb.blur_attribute = "PostPosition"
    # intrinsic spatial resolution at 140 keV for 9.5 mm thick NaI
    sb.blur_fwhm = 3.9 * mm
    sb.keep_in_solid_limits = True
    sb.use_truncated_Gaussian = False

    # energy windows (Energy range. 35-588 keV)
    cc = digitizer.add_module("DigitizerEnergyWindowsActor", f"{name}_energy_window")
    channels = [
        {"name": f"scatter", "min": 108.57749938965 * keV, "max": 129.5924987793 * keV},
        {"name": f"peak140", "min": 129.5924987793 * keV, "max": 150.60751342773 * keV},
    ]
    if not spectrum_channel:
        channels.pop(0)
    cc.channels = channels

    # projection
    proj = digitizer.add_module("DigitizerProjectionActor", f"{name}_projection")
    channel_names = [c["name"] for c in channels]
    proj.input_digi_collections = channel_names
    proj.spacing = [4.7951998710632 * mm / 2, 4.7951998710632 * mm / 2]
    proj.size = [256, 256]
    # by default, the origin of the images are centered
    # set to False here to keep compatible with previous version
    # proj.origin_as_image_center = False
    # projection plane: it depends on how the spect device is described
    # here, we need this rotation
    proj.detector_orientation_matrix = Rotation.from_euler(
        "yx", (90, 90), degrees=True
    ).as_matrix()
    proj.write_to_disk = True

    # end
    return digitizer


def add_digitizer_v4(sim, crystal_name, name, spectrum_channel=True):
    # create main chain
    mm = g4_units.mm
    digitizer = Digitizer(sim, crystal_name, name)

    # Singles
    sc = digitizer.add_module("DigitizerAdderActor", f"{name}_singles")
    sc.group_volume = None
    sc.policy = "EnergyWinnerPosition"

    # detection efficiency
    # ea = digitizer.add_module("DigitizerEfficiencyActor")
    # ea.efficiency = 0.86481  # FAKE

    # energy blurring
    keV = g4_units.keV
    eb = digitizer.add_module("DigitizerBlurringActor")
    eb.blur_attribute = "TotalEnergyDeposit"
    eb.blur_method = "InverseSquare"
    eb.blur_resolution = 0.099  # in %
    eb.blur_reference_value = 140.5 * keV

    # spatial blurring
    # Source: HE4SPECS - FWHM = 3.9 mm
    # FWHM = 2.sigma.sqrt(2ln2) -> sigma = 1.656 mm
    sb = digitizer.add_module("DigitizerSpatialBlurringActor")
    sb.blur_attribute = "PostPosition"
    # intrinsic spatial resolution at 140 keV for 9.5 mm thick NaI
    sb.blur_fwhm = 3.6 * mm
    sb.keep_in_solid_limits = True
    sb.use_truncated_Gaussian = False

    # energy windows (Energy range. 35-588 keV)
    cc = digitizer.add_module("DigitizerEnergyWindowsActor", f"{name}_energy_window")
    channels = [
        {"name": f"scatter", "min": 108.57749938965 * keV, "max": 129.5924987793 * keV},
        {"name": f"peak140", "min": 129.5924987793 * keV, "max": 150.60751342773 * keV},
    ]
    if not spectrum_channel:
        channels.pop(0)
    cc.channels = channels

    # projection
    proj = digitizer.add_module("DigitizerProjectionActor", f"{name}_projection")
    channel_names = [c["name"] for c in channels]
    proj.input_digi_collections = channel_names
    proj.spacing = [4.7951998710632 * mm / 2, 4.7951998710632 * mm / 2]
    proj.size = [256, 256]

    # projection plane: it depends on how the spect device is described
    # here, we need this rotation
    proj.detector_orientation_matrix = Rotation.from_euler(
        "yx", (90, 90), degrees=True
    ).as_matrix()
    proj.write_to_disk = True

    # end
    return digitizer


def update_digitizer_energy_windows(digitizer, channels):
    cc = digitizer.find_module_by_type("DigitizerEnergyWindowsActor")
    print(cc)
    cc.channels = channels


def compute_plane_position_and_distance_to_crystal(collimator_type):
    sim = Simulation()
    spect, colli, crystal = add_spect_head(sim, "spect", collimator_type, debug=True)
    pos = get_volume_position_in_head(sim, "spect", f"collimator", "min", axis=0)
    y = get_volume_position_in_head(sim, "spect", "crystal", "center", axis=0)
    crystal_distance = y - pos
    psd = spect.size[2] / 2.0 - pos
    return pos, crystal_distance, psd


def add_detection_plane_for_arf(sim, det_name, colli_type, plane_size=None):
    # user plane size only for debug purpose
    mm = g4_units.mm
    if plane_size is None:
        plane_size = [533 * mm, 387 * mm]

    # plane
    nm = g4_units.nm
    detector_plane = sim.add_volume("Box", det_name)
    detector_plane.material = "G4_Galactic"
    detector_plane.color = [1, 0, 0, 1]
    detector_plane.size = [1 * nm, plane_size[0], plane_size[1]]

    # compute the correct position according to the collimator
    pos, _, _ = compute_plane_position_and_distance_to_crystal(colli_type)
    detector_plane.translation = [0, pos, 0]

    return detector_plane


def add_source_for_arf_training_dataset(
    sim, source_name, activity, detector_plane, min_energy, max_energy
):
    cm = g4_units.cm
    source = sim.add_source("GenericSource", source_name)
    source.particle = "gamma"
    source.activity = activity
    source.position.type = "disc"
    source.position.radius = 5 * cm
    source.position.translation = [0, -20 * cm, 0]
    source.direction.type = "iso"
    source.energy.type = "range"
    source.energy.min_energy = min_energy
    source.energy.max_energy = max_energy
    source.direction.acceptance_angle.volumes = [detector_plane.name]
    source.direction.acceptance_angle.intersection_flag = True

    return source


def add_actor_for_arf_training_dataset(sim, colli_type, ene_win_actor, rr):
    mm = g4_units.mm

    # WARNING head must be in a specific position, because the detector plane
    # is in a parallel world, not attached to the head

    # detector input plane
    sim.add_parallel_world("arf_world")
    # detector_plane = add_detection_plane_for_arf(
    #   sim, "arf_plane", plane_size=[1533, 1387]) # for debug
    detector_plane = add_detection_plane_for_arf(sim, "arf_plane", colli_type)
    detector_plane.color = [0, 1, 0, 1]
    detector_plane.mother = "arf_world"
    rotate_gantry(detector_plane, radius=0, start_angle_deg=0)

    # set the position in front of the collimator
    pos, _, _ = compute_plane_position_and_distance_to_crystal(colli_type)
    detector_plane.translation = [0, pos, 0]

    # arf actor for building the training dataset
    arf = sim.add_actor("ARFTrainingDatasetActor", "ARF (training)")
    arf.energy_windows_actor = ene_win_actor.name
    arf.attached_to = detector_plane.name
    arf.output_filename = f"arf_training_dataset.root"
    arf.russian_roulette = rr
    # arf.plane_axis = [0, 1, 2] -> no ?
    # arf.plane_axis = [0, 2, 1]
    arf.plane_axis = [1, 2, 0]  # -> seems ok

    return detector_plane, arf


def add_arf_detector(sim, name, colli_type, image_size, image_spacing, pth_filename):
    # create the plane
    det_plane = add_detection_plane_for_arf(sim, name, colli_type)

    # set the position in front of the collimator
    _, crystal_distance, _ = compute_plane_position_and_distance_to_crystal(colli_type)
    rotate_gantry(det_plane, radius=0, start_angle_deg=0)

    arf = sim.add_actor("ARFActor", f"{name}_arf")
    arf.attached_to = det_plane.name
    arf.output_filename = f"projection_{arf.name}.mhd"
    arf.batch_size = 1e5
    arf.image_size = image_size
    arf.image_spacing = image_spacing
    arf.verbose_batch = False
    arf.distance_to_crystal = crystal_distance  # 74.625 * mm
    arf.pth_filename = pth_filename
    arf.flip_plane = False
    arf.plane_axis = [1, 2, 0]
    arf.gpu_mode = "auto"

    return det_plane, arf


def rotate_gantry(
    head, radius, start_angle_deg, step_angle_deg=1, nb_angle=1, initial_rotation=None
):
    """
    This function rotates the gantry both for 1) conventional spect or 2) ARF plane,
    according to the value of initial_rotation
    """
    # compute the nb translation and rotation
    translations = []
    rotations = []

    if initial_rotation is None:
        initial_rotation = Rotation.from_euler("xz", (180, 90), degrees=True)

    current_angle_deg = start_angle_deg
    for r in range(nb_angle):
        tr = head.translation.copy()
        tr[1] += radius
        t, rot = get_transform_orbiting(tr, "Z", current_angle_deg)
        rot = Rotation.from_matrix(rot)
        rot = rot * initial_rotation
        rot = rot.as_matrix()
        translations.append(t)
        rotations.append(rot)
        current_angle_deg += step_angle_deg

    # set the motion for the SPECT head
    if nb_angle > 1:
        head.add_dynamic_parametrisation(translation=translations, rotation=rotations)

    # we set the initial position in all cases, this allows for check_overlap to be done
    # with the first position
    head.translation = translations[0]
    head.rotation = rotations[0]


def add_intevo_digitizer_lu177_v3(sim, crystal_name, name, spectrum_channel=False):
    keV = g4_units.keV
    proj, singles_ene_windows = add_intevo_digitizer_v3(sim, crystal_name, name)
    channels = [
        {"name": f"spectrum", "min": 3 * keV, "max": 515 * keV},
        {"name": f"scatter1_{name}", "min": 96 * keV, "max": 104 * keV},
        {"name": f"peak113_{name}", "min": 104.52 * keV, "max": 121.48 * keV},
        {"name": f"scatter2_{name}", "min": 122.48 * keV, "max": 133.12 * keV},
        {"name": f"scatter3_{name}", "min": 176.46 * keV, "max": 191.36 * keV},
        {"name": f"peak208_{name}", "min": 192.4 * keV, "max": 223.6 * keV},
        {"name": f"scatter4_{name}", "min": 224.64 * keV, "max": 243.3 * keV},
    ]
    if not spectrum_channel:
        channels.pop(0)
    singles_ene_windows.channels = channels
    proj.input_digi_collections = [x["name"] for x in channels]

    return proj


def add_intevo_digitizer_lu177_v4(sim, crystal_name, name, spectrum_channel=False):
    keV = g4_units.keV
    proj, singles_ene_windows = add_intevo_digitizer_v3(sim, crystal_name, name)
    channels = [
        {"name": f"scatter1_{name}", "min": 84.75 * keV, "max": 101.7 * keV},
        {"name": f"peak113_{name}", "min": 101.7 * keV, "max": 124.3 * keV},
        {"name": f"scatter2_{name}", "min": 124.3 * keV, "max": 141.25 * keV},
        {"name": f"scatter3_{name}", "min": 145.6 * keV, "max": 187.2 * keV},
        {"name": f"peak208_{name}", "min": 187.2 * keV, "max": 228.8 * keV},
        {"name": f"scatter4_{name}", "min": 228.8 * keV, "max": 270.4 * keV},
    ]
    if not spectrum_channel:
        channels.pop(0)
    singles_ene_windows.channels = channels
    proj.input_digi_collections = [x["name"] for x in channels]

    return proj


def get_channels_lu177_v4(name="ew"):
    keV = g4_units.keV
    return [
        {"name": f"scatter1_{name}", "min": 84.75 * keV, "max": 101.7 * keV},
        {"name": f"peak113_{name}", "min": 101.7 * keV, "max": 124.3 * keV},
        {"name": f"scatter2_{name}", "min": 124.3 * keV, "max": 141.25 * keV},
        {"name": f"scatter3_{name}", "min": 145.6 * keV, "max": 187.2 * keV},
        {"name": f"peak208_{name}", "min": 187.2 * keV, "max": 228.8 * keV},
        {"name": f"scatter4_{name}", "min": 228.8 * keV, "max": 270.4 * keV},
    ]


def add_intevo_digitizer_tc99m_v3(sim, crystal_name, name, spectrum_channel=False):
    keV = g4_units.keV
    proj, singles_ene_windows = add_intevo_digitizer_v3(sim, crystal_name, name)
    channels = [
        {"name": f"spectrum", "min": 3 * keV, "max": 160 * keV},
        {"name": f"scatter", "min": 108.57749938965 * keV, "max": 129.5924987793 * keV},
        {"name": f"peak140", "min": 129.5924987793 * keV, "max": 150.60751342773 * keV},
    ]
    if not spectrum_channel:
        channels.pop(0)
    singles_ene_windows.channels = channels
    proj.input_digi_collections = [x["name"] for x in channels]

    return proj


def add_intevo_digitizer_v3(sim, crystal_name, name):
    # hits
    hits = sim.add_actor("DigitizerHitsCollectionActor", f"hits_{name}")
    hits.attached_to = crystal_name
    hits.output_filename = ""  # No output
    hits.attributes = [
        "PostPosition",
        "TotalEnergyDeposit",
        "PreStepUniqueVolumeID",
        "PostStepUniqueVolumeID",
        "GlobalTime",
        "Weight",  # required when using VRT techniques such as Free Flight
    ]

    # singles
    singles = sim.add_actor("DigitizerAdderActor", f"singles_{name}")
    singles.attached_to = crystal_name
    singles.input_digi_collection = hits.name
    # sc.policy = "EnergyWeightedCentroidPosition"
    singles.policy = "EnergyWinnerPosition"
    singles.output_filename = ""  # No output
    singles.group_volume = None

    # efficiency actor
    # eff = sim.add_actor("DigitizerEfficiencyActor", f"singles_{name}_eff")
    # eff.attached_to = crystal_name
    # eff.input_digi_collection = singles.name
    # eff.efficiency = 0.86481  # FIXME probably wrong, to evaluate
    # eff.efficiency = 1.0
    # eff.output_filename = ""  # No output

    # energy blur
    keV = g4_units.keV
    MeV = g4_units.MeV
    ene_blur = sim.add_actor("DigitizerBlurringActor", f"singles_{name}_eblur")
    ene_blur.output_filename = ""
    ene_blur.attached_to = crystal_name
    ene_blur.input_digi_collection = singles.name
    ene_blur.blur_attribute = "TotalEnergyDeposit"
    ene_blur.blur_method = "Linear"
    ene_blur.blur_resolution = 0.13
    ene_blur.blur_reference_value = 80 * keV
    ene_blur.blur_slope = -0.09 * 1 / MeV

    # spatial blurring
    mm = g4_units.mm
    spatial_blur = sim.add_actor(
        "DigitizerSpatialBlurringActor", f"singles_{name}_sblur"
    )
    spatial_blur.output_filename = ""
    spatial_blur.attached_to = crystal_name
    spatial_blur.input_digi_collection = ene_blur.name
    spatial_blur.blur_attribute = "PostPosition"
    spatial_blur.blur_fwhm = 3.9 * mm
    spatial_blur.keep_in_solid_limits = True
    spatial_blur.use_truncated_Gaussian = False

    # energy windows
    singles_ene_windows = sim.add_actor(
        "DigitizerEnergyWindowsActor", f"{name}_energy_window"
    )
    singles_ene_windows.attached_to = crystal_name
    singles_ene_windows.input_digi_collection = spatial_blur.name
    singles_ene_windows.output_filename = ""  # No output

    # projection
    proj = sim.add_actor("DigitizerProjectionActor", f"{name}_projection")
    proj.attached_to = crystal_name
    proj.spacing = [4.7951998710632 * mm / 2, 4.7951998710632 * mm / 2]
    proj.size = [128 * 2, 128 * 2]
    proj.output_filename = "projection.mhd"
    proj.origin_as_image_center = True

    # plane orientation
    proj.detector_orientation_matrix = Rotation.from_euler(
        "yx", (90, 90), degrees=True
    ).as_matrix()

    return proj, singles_ene_windows


def get_pytomography_detector_physics_data(colli_name):
    cm = g4_units.cm
    # create a fake simulation to get the volume information
    sim = Simulation()
    det, colli, crystal = add_spect_head(sim, f"fake", collimator_type=colli_name)
    holep = sim.volume_manager.find_volumes("collimator_hole1_param")[0]
    hole = sim.volume_manager.find_volumes("collimator_hole1")[0]
    d = {
        "hole_shape": 6,
        "hole_diameter": hole.radius * 2 / cm,
        "hole_spacing": holep.translation[1] / cm,
        "collimator_thickness": hole.height / cm,
        "collimator_material": colli.material.lower(),
        "crystal_width": crystal.size[1] / cm,
        "crystal_height": crystal.size[2] / cm,
    }

    return d


def add_digitizer(
    sim, crystal_name, name=None, size=None, spacing=None, channels=None, filename=None
):
    # default parameters
    mm = g4_units.mm
    if name is None:
        name = crystal_name
    if size is None:
        size = [128, 128]
    if spacing is None:
        spacing = [4.7951998710632 * mm, 4.7951998710632 * mm]
    if channels is None:
        channels = get_default_energy_windows("tc99m")

    # create the main digitizer chain
    digitizer = Digitizer(sim, crystal_name, name)

    # Singles
    sc = digitizer.add_module("DigitizerAdderActor", f"{name}_singles")
    sc.group_volume = None
    sc.policy = "EnergyWinnerPosition"

    # detection efficiency
    # ea = digitizer.add_module("DigitizerEfficiencyActor")
    # ea.efficiency = 0.86481  # FAKE

    # energy blurring
    keV = g4_units.keV
    eb = digitizer.add_module("DigitizerBlurringActor", f"{name}_eblur")
    eb.blur_attribute = "TotalEnergyDeposit"
    eb.blur_method = "InverseSquare"
    eb.blur_resolution = 0.099  # in %
    eb.blur_reference_value = 140.5 * keV
    # alternative :
    # eb.blur_method = "Linear"
    # eb.blur_resolution = 0.13
    # eb.blur_reference_value = 80 * keV
    # eb.blur_slope = -0.09 * 1 / MeV

    # spatial blurring
    # Source: HE4SPECS - FWHM = 3.9 mm or 3.6 mm?
    # FWHM = 2.sigma.sqrt(2ln2) -> sigma = 1.656 mm
    sb = digitizer.add_module("DigitizerSpatialBlurringActor", f"{name}_sblur")
    sb.blur_attribute = "PostPosition"
    # intrinsic spatial resolution at 140 keV for 9.5 mm thick NaI
    sb.blur_fwhm = 3.6 * mm
    sb.keep_in_solid_limits = True
    sb.use_truncated_Gaussian = False

    # default energy windows (Energy range. 35-588 keV)
    cc = digitizer.add_module("DigitizerEnergyWindowsActor", f"{name}_energy_window")
    cc.channels = channels

    # projection
    proj = digitizer.add_module("DigitizerProjectionActor", f"{name}_projection")
    channel_names = [c["name"] for c in channels]
    proj.input_digi_collections = channel_names
    proj.spacing = spacing
    proj.size = size
    proj.write_to_disk = True
    if filename is not None:
        proj.output_filename = filename

    # projection plane: it depends on how the spect device is described
    # here, we need this rotation
    proj.detector_orientation_matrix = Rotation.from_euler(
        "yx", (90, 90), degrees=True
    ).as_matrix()

    return digitizer
