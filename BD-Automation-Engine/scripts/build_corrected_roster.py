"""Build corrected contract roster matching roster entries to federal contracts with Bullhorn intel."""
import csv
import os

rows = [
    # COLIN (5 programs - was missing VMOD, GENMOD; had wrong UNNOD/CENNOD)
    ['Colin', 'BIM', 'BIM', 'Base Infrastructure Modernization', 'CACI', 'Air Force / EITaaS', '$12.5B IDIQ', 'Established', 'Modernize DoD base area network. CACI $212M Space Force task order Jan 2026. 23 awardees.', '1 placement (BIM TO2/TO3)'],
    ['Colin', 'BICES', 'BICES', 'Battlefield Information Collection & Exploitation System', 'GDIT', 'DIA / DoD', '~$200M+', 'Established', 'NATO/DIA intelligence sharing. 2nd highest placement count in Bullhorn.', '164 placements, 7 call notes'],
    ['Colin', 'AFCENT', 'AFCENT', 'Air Forces Central Command IT/Cyber Support', 'CACI', 'Air Force / CENTCOM', 'Varies', 'Established', 'USAF CENTCOM theater IT/cyber. Linked to SCORPION cyber task.', '3 call notes, 2 placements'],
    ['Colin', 'VMOD', 'VMOD', 'Vehicle Modernization (probable Army/CACI program)', 'CACI', 'Army / DoD', 'Unknown', 'Established', 'CACI vehicle/platform modernization. Not in Bullhorn. Verify full name.', 'No Bullhorn data'],
    ['Colin', 'GENMOD', 'GENMOD', 'General Modernization (probable)', 'CACI', 'DoD', 'Unknown', 'New Add', 'CACI modernization program. Not in Bullhorn. Verify full name.', 'No Bullhorn data'],

    # KEVIN (3 programs - correct)
    ['Kevin', 'NGEN', 'NGEN-R SMIT', 'Navy Next Generation Enterprise Network', 'Leidos', 'Navy', '$7.7B', 'Established', 'Navy enterprise IT modernization. Proven pipeline.', '25 placements, 62 call notes'],
    ['Kevin', 'DES', 'DES', 'Defense Enclave Services', 'Leidos', 'DISA', '$11.5B', 'Established', 'Fourth Estate IT consolidation. Major program.', '76 placements total'],
    ['Kevin', 'I3TS', 'I3TS', 'DTRA Integrated IT Support Services', 'Leidos/GDIT', 'DTRA', '~$500M+', 'Established', 'DTRA IT support at JBAB. HIGHEST placement count in Bullhorn.', '315 placements - #1 program'],

    # JUSTIN (6 programs - PNT E41 not E+I)
    ['Justin', 'Horizon II', 'Horizon II', 'Horizon II Network Engineering Program', 'Leidos', 'DoD', 'Unknown', 'Established', 'Leidos network/infrastructure program.', '38 call notes'],
    ['Justin', 'EDIS', 'EDIS', 'Enterprise Data & Information Services', 'Unknown', 'DoD', 'Unknown', 'Established', '128 call notes (may include false positives).', '128 call notes (verify)'],
    ['Justin', 'Scorpion', 'SCORPION', 'AFCENT Scorpion Cyber Task (ISSO/ISSM)', 'Various', 'Air Force / CENTCOM', 'Unknown', 'Established', 'AFCENT cyber/ISSO support.', '334 call notes, 2 placements'],
    ['Justin', 'RITS', 'RITS', 'Regional IT Services (Air Force)', 'Various', 'Air Force', 'Unknown', 'Established', 'Air Force Regional IT Services.', '293 call notes'],
    ['Justin', 'DTAM', 'DTAM', 'Defense Travel Administration/Management', 'Unknown', 'DoD', 'Unknown', 'Established', 'Mentioned alongside GMASS. Small presence.', '2 call notes'],
    ['Justin', 'PNT E41', 'PNT E&I', 'Position, Navigation & Timing Engineering & Integration', 'Unknown', 'DoD / Space Force', 'Unknown', 'New Add', 'GPS/PNT defense program. "E41" likely OCR of "E&I".', '1 call note'],

    # ANDRES (6 programs - VC25B not V625B, DA & Cruise Missiles not BA+Cruise Mint)
    ['Andres', 'VC25B', 'VC-25B', 'VC-25B Presidential Aircraft Replacement (Air Force One)', 'Boeing', 'Air Force', '$5.3B', 'Established', 'Boeing next-gen Air Force One replacement. Major defense program.', 'No direct Bullhorn data'],
    ['Andres', 'SLS', 'SLS', 'Space Launch System', 'Boeing', 'NASA', '$20B+', 'Established', 'NASA heavy-lift rocket.', '43 call notes'],
    ['Andres', 'Stingray', 'MQ-25 Stingray', 'MQ-25 Stingray Unmanned Aerial Refueling', 'Boeing', 'Navy', '$13B', 'Established', 'Boeing MQ-25. Meeting with Alex Tubbs/Brian Herman noted.', '2 call notes, BD meeting'],
    ['Andres', 'SI + WS', 'SI + WS', 'Systems Integration + Weapon Systems', 'Boeing', 'DoD', 'Unknown', 'Established', 'Boeing SI & Weapon Systems division. Verify specific program.', 'No Bullhorn data'],
    ['Andres', 'B-52', 'B-52', 'B-52 Stratofortress Modernization (CERP)', 'Boeing', 'Air Force', '$2.6B+', 'Established', 'B-52 re-engining and modernization.', 'No direct Bullhorn data'],
    ['Andres', 'DA & Cruise Missiles', 'DA & Cruise Missiles', 'Boeing Defense/Attack & Cruise Missile Programs', 'Boeing', 'Air Force', 'Classified', 'Established', 'Boeing cruise missile programs (LRSO/AGM-181). "DA" = Defense/Attack.', 'No Bullhorn data'],

    # CAPELLUTO (5 programs - correct, was "Cap" in manual)
    ['Capelluto', 'MCEN', 'MCEN', 'Marine Corps Enterprise Network', 'Leidos', 'Marines', '$6.5B', 'Established', 'Marine Corps enterprise IT. Active with proven placements.', '25 placements, 29 call notes'],
    ['Capelluto', 'DCPDS', 'DCPDS', 'Defense Civilian Personnel Data System', 'Leidos', 'Army / DoD', '~$100M+', 'Established', 'Oracle-based HR system.', '1 job in Bullhorn'],
    ['Capelluto', 'ALTESS', 'ALTESS', 'Army Logistics Technology Enterprise Systems & Services', 'IBM', 'Army', '~$500M', 'Established', 'Army IT hosting/cloud services.', '14 placements, 3 call notes'],
    ['Capelluto', 'SCITES', 'SCITES', 'SOUTHCOM IT Enterprise Services', 'ManTech', 'SOUTHCOM', '~$100M+', 'New Add', 'ManTech SOUTHCOM support. Active cold-calling.', '38 call notes'],
    ['Capelluto', 'NASA', 'Leidos NASA', 'Leidos NASA Contract (SENSE or other)', 'Leidos', 'NASA', 'Varies', 'New Add', 'Could be SENSE, ATOP, or other. 11 placements for SENSE.', '11 placements (SENSE)'],

    # GULLETTE (6 programs - correct)
    ['Gullette', 'AFNCR', 'AFNCR', 'Air Force National Capital Region IT Support', 'Leidos', 'Air Force', '~$300M', 'Established', '29 placements. Multiple active jobs. Andrews AFB. Very active.', '29 placements, active jobs'],
    ['Gullette', 'ASA ALT', 'ASA(ALT)', 'Asst Secretary of the Army - Acquisition, Logistics & Tech', 'Various', 'Army', 'Varies', 'Established', 'Army acquisition support.', 'No direct Bullhorn data'],
    ['Gullette', 'INSITE', 'INSITE', 'INSITE (IC program)', 'Various', 'IC / DoD', 'Unknown', 'Established', 'TS/SCI pen testing roles. IC program.', '5 call notes'],
    ['Gullette', 'BOA', 'BOA', 'Basic Ordering Agreement (Staff Augmentation)', 'Northrop Grumman', 'Various', 'Varies', 'Established', 'Northrop Grumman surge staffing vehicle.', '8 placements'],
    ['Gullette', 'JTAGS', 'JTAGS', 'Joint Tactical Ground Station', 'Various', 'Army / MDA', '~$200M', 'Established', 'Missile defense early warning system.', '5 call notes'],
    ['Gullette', 'Cloud One', 'Cloud One', 'Air Force Cloud One / Platform One', 'Various', 'Air Force', '$1B+', 'New Add', 'AF DevSecOps cloud initiative.', '36 placements, 3 call notes'],

    # STEPH (7 programs - HUD Central not Hub Central, FAA MISCIV not NISCIV, ANTYPY-2 not TRX ANR XRYA-2, DEOS not DCGS, BAG ISC not BAE ISC)
    ['Steph', 'HUD Central', 'HUD Central', 'HUD Central IT Support (Dept of Housing & Urban Development)', 'Unknown', 'HUD', 'Unknown', 'Established', 'HUD IT services. Not "Hub Central". No Bullhorn matches.', 'No Bullhorn data'],
    ['Steph', 'GA Power', 'GA Power', 'General Atomics Power/Energy Program', 'General Atomics', 'DoD / DOE', 'Unknown', 'Established', '4 call notes mention General Atomics.', '4 call notes'],
    ['Steph', 'FAA MISCIV', 'FAA MISCIV', 'FAA Mission & Infrastructure Support (MISCIV)', 'Unknown', 'FAA', 'Unknown', 'Established', 'OCR read as NISCIV but roster says MISCIV. FAA support contract. 4 notes for NISC variant.', '4 call notes (NISC)'],
    ['Steph', 'ANTYPY-2', 'ANTYPY-2', 'RTX Raytheon ANTYPY-2 Program', 'RTX/Raytheon', 'DoD', 'Unknown', 'Established', 'NOT "TRX ANR XRYA-2". Raytheon classified program. No Bullhorn matches.', 'No Bullhorn data'],
    ['Steph', 'BAG ISC', 'BAG ISC', 'BAG ISC Program (not BAE ISC)', 'Unknown', 'Unknown', 'Unknown', 'Established', 'Roster says BAG ISC not BAE ISC. Could still be BAE I&S. Verify.', 'No Bullhorn data'],
    ['Steph', 'DEOS', 'DEOS', 'GDIT Defense Enterprise Office Solutions (DEOS/DOD365)', 'GDIT', 'DISA / DoD', '$4.5B+', 'Established', 'NOT DCGS! Roster says DEOS. DoD Office 365 migration. 61 placements for DOD365 in Bullhorn.', '61 placements (DOD365)'],
    ['Steph', 'TARPON', 'RTX TARPON', 'RTX Raytheon TARPON Program', 'RTX/Raytheon', 'DoD', 'Unknown', 'Established', 'Raytheon program. No Bullhorn matches.', 'No Bullhorn data'],

    # LOGAN (10 programs - ARC not Deloitte ACC, NAVY FIP IV not FPIV, JSFACE not JSFACS, EPA MAINES not EPA MAINS)
    ['Logan', 'JUSTIFIED', 'JUSTIFIED', 'GDIT Justified IT Services Program', 'GDIT', 'Air Force', '~$1B+', 'Established', 'TOP program in Bullhorn. Positions in Dayton, Hanscom, JBAB.', '994 call notes - #1 program'],
    ['Logan', 'INSCOM', 'INSCOM', 'Army Intelligence & Security Command Support', 'Various', 'Army', '$1B+', 'Established', 'Active cold-calling for INSCOM and RS3 support.', '34 call notes'],
    ['Logan', 'WARHAWK', 'WARHAWK', 'Warhawk Program (Leidos)', 'Leidos', 'DoD / IC', 'Unknown', 'Established', 'Very active. Software dev job reqs. Significant pipeline.', '222 call notes, active jobs'],
    ['Logan', 'AIRDROP', 'AIRDROP', 'Unknown program', 'Unknown', 'DoD', 'Unknown', 'Established', 'No Bullhorn matches. Possibly classified.', 'No Bullhorn data'],
    ['Logan', 'ARC', 'ARC', 'Deloitte ARC Program', 'Deloitte', 'DoD / Federal', 'Unknown', 'New Add', 'NOT "Deloitte ACC". Roster says ARC. Deloitte federal consulting.', 'No Bullhorn data'],
    ['Logan', 'CDET III', 'CDET III', 'CDET III Program', 'Unknown', 'DoD', 'Unknown', 'New Add', 'Verify full program name.', '1 call note'],
    ['Logan', 'NAVY FIP IV', 'NAVY FIP IV', 'Navy Fleet Information Platform IV (probable)', 'Unknown', 'Navy', 'Unknown', 'Established', 'Roster says FIP IV not FPIV. Navy IT/information platform.', 'No Bullhorn data'],
    ['Logan', 'JSFACE', 'JSFACE', 'Unknown (roster confirms JSFACE not JSFACS)', 'Unknown', 'DoD', 'Unknown', 'Established', 'Roster confirms JSFACE spelling. Verify full name.', 'No Bullhorn data'],
    ['Logan', 'EPA MAINES', 'EPA MAINES', 'EPA Maintenance & Infrastructure Services', 'Unknown', 'EPA', 'Unknown', 'Established', 'EPA IT infrastructure. "MAINES" not "MAINS".', '7 call notes (MAINS)'],
    ['Logan', 'EPA WI CRD GLO', 'EPA WI CRD GLO', 'EPA WI CRD Global Operations', 'Unknown', 'EPA', 'Unknown', 'Established', 'EPA program. Verify full name with Logan.', '41 call notes (WIRED)'],

    # HOPPE / Emily (3 programs - person is "Hoppe" not "Emily")
    ['Hoppe', 'Palantir', 'PALANTIR', 'Palantir Technologies Defense Programs (Gotham/Foundry)', 'Palantir', 'DoD / IC', '$1B+', 'Established', 'Very active across DoD/IC.', '425 call notes'],
    ['Hoppe', 'DC3', 'DC3', 'Defense Cyber Crime Center', 'Various', 'DoD', '~$500M', 'Established', 'Cyber forensics/investigations. Digital Forensics roles.', '560 call notes, 1 placement'],
    ['Hoppe', 'CDC', 'CDC', 'Centers for Disease Control IT Support', 'Leidos', 'HHS / CDC', 'Varies', 'New Add', 'Leidos CDC presence.', '1 active job listing'],

    # TREVOR top board (7 programs - DRT GRASP confirmed, FAA BNIACTS not BNACTS, Arc Field confirmed)
    ['Trevor', 'BAE ISC', 'BAE ISC', 'BAE Systems Intelligence & Security Contract', 'BAE', 'IC / DoD', 'Unknown', 'Established', 'BAE I&S division.', 'No direct Bullhorn data'],
    ['Trevor', 'DRT GRASP', 'DRT GRASP', 'DRT GRASP Program (roster confirms DRT not DTRA)', 'Unknown', 'Unknown', 'Unknown', 'Established', 'Roster says DRT not DTRA. Could still be DTRA-related. Verify.', '1 call note'],
    ['Trevor', 'OCIO', 'OCIO', 'Office of the CIO (agency IT support)', 'Various', 'Various', 'Varies', 'Established', 'Verify which agency.', 'Needs agency clarification'],
    ['Trevor', 'SENSE', 'SENSE', 'NASA Space Network Evolution', 'Leidos', 'NASA', '~$500M', 'Established', 'Leidos NASA space comms modernization.', '11 placements, 61 call notes'],
    ['Trevor', 'First Responder', 'First Responder', 'Peraton First Responder Solutions', 'Peraton', 'DHS / FEMA', 'Unknown', 'Established', 'Peraton first responder tech/comms.', '2 call notes'],
    ['Trevor', 'Arc Field', 'ARCFIELD', 'Arcfield Various IC/DoD Programs', 'Arcfield', 'IC / DoD', 'Unknown', 'Established', 'Defense contractor (formerly SAIC/Engility).', '24 call notes'],
    ['Trevor', 'FAA BNIACTS', 'FAA BNIACTS', 'FAA Base/National Airspace Communications', 'Peraton', 'FAA', 'Unknown', 'New Add', 'Roster says BNIACTS not BNACTS. Peraton FAA comms.', '1 call note'],

    # IDK (3 programs - NTT NNIS not NAIS, Peraton DCLO not BECO/DECO)
    ['IDK', 'JUSTIFIED', 'JUSTIFIED', 'GDIT Justified IT Services Program', 'GDIT', 'Air Force', '~$1B+', 'Established', 'Same as Logan. Top Bullhorn program.', '994 call notes'],
    ['IDK', 'NTT NNIS', 'NTT NNIS', 'NTT Data NNIS Program', 'NTT', 'Various', 'Unknown', 'Established', 'Roster says NNIS not NAIS. NTT Data defense program. Verify.', '1 call note'],
    ['IDK', 'Peraton DCLO', 'Peraton DCLO', 'Peraton DCLO Program (NOT BECO/DECO)', 'Peraton', 'Navy / DoD', 'Unknown', 'Established', 'Roster says DCLO not BECO/DECO. Peraton defense comms. 71 DECO notes may be related.', '71 DECO call notes (related?)'],

    # EMMA (9 programs - GSMO TNIS and TNO1 not TN15/TN0)
    ['Emma', 'Dell', 'DELL', 'Dell Technologies Federal Programs', 'Dell', 'Various', 'Varies', 'Established', 'Dell federal IT hardware/services.', '26 call notes'],
    ['Emma', 'THD', 'THD', 'Unknown - verify with Emma', 'Unknown', 'Unknown', 'Unknown', 'Established', 'Context unclear. Verify meaning.', '3 call notes (unclear)'],
    ['Emma', 'HPE', 'HPE', 'Hewlett Packard Enterprise Federal', 'HPE', 'Various', 'Varies', 'Established', 'Cloud Advisory. Active BD.', '12 call notes'],
    ['Emma', 'UPS Cap', 'UPS Capital', 'UPS Capital Technology Services', 'UPS', 'Commercial', 'Unknown', 'Established', 'Active contract extension at 2-year mark.', '2 call notes'],
    ['Emma', 'GSMO TNIS', 'GSMO TN15', 'DISA GSM-O II Task Number 15 (probable)', 'Leidos', 'DISA', 'Part of $4.3B GSMO II', 'Established', 'Roster says TNIS. Likely TN15 or TN1S. Part of GSMO II umbrella.', '511 notes, 106 placements (all GSMO)'],
    ['Emma', 'GSMO TNO1', 'GSMO TN01', 'DISA GSM-O II Task Number 01', 'Leidos', 'DISA', 'Part of $4.3B GSMO II', 'Established', 'Roster says TNO1 (TN01). SATCOM NOC Technician job at Hill AFB.', 'Active job (SATCOM NOC)'],
    ['Emma', 'Emory Uni', 'Emory University', 'GSMO / Emory University IT Support', 'Leidos', 'DISA / Emory', 'Part of GSMO', 'Established', 'GSM-O task at Emory University.', '2 call notes'],
    ['Emma', 'RTX TEE', 'RTX TEE', 'RTX Raytheon TEE Program', 'RTX', 'DoD', 'Unknown', 'New Add', 'Raytheon Technologies program. Verify.', 'No Bullhorn data'],
    ['Emma', 'AFS RITS', 'AFS RITS', 'Air Force Space RITS', 'Various', 'Air Force / Space Force', 'Unknown', 'New Add', 'Air Force Space + RITS combination.', '293 call notes (RITS)'],

    # TREVOR W (7 programs - has NISST which is new, SCITLS = SCITES)
    ['Trevor W', 'SSC', 'SSC', 'Space Systems Command', 'Various', 'Space Force', 'Varies', 'Established', 'Space Force IT/engineering support.', '7 call notes'],
    ['Trevor W', 'SCITLS', 'SCITES', 'SOUTHCOM IT Enterprise Services (misspelling)', 'ManTech', 'SOUTHCOM', '~$100M+', 'Established', 'ManTech SCITES. Roster confirms SCITLS spelling.', '38 call notes'],
    ['Trevor W', 'NISST', 'NISST', 'Unknown - New Add (possibly NIST-related)', 'Unknown', 'Unknown', 'Unknown', 'New Add', 'Not in my original list. Could be NIST or NISC variant. Verify.', 'No Bullhorn data'],
    ['Trevor W', 'F-35 Cyber', 'F-35 Cyber', 'F-35 Lightning II Cybersecurity', 'Lockheed Martin', 'DoD', 'Part of $1.7T F-35', 'New Add', 'JSF cyber defense.', '4 call notes'],
    ['Trevor W', 'DLA JETS', 'DLA JETS', 'DLA J6 Enterprise Technology Services', 'Various', 'DLA / DoD', '~$500M', 'Established', 'Defense Logistics Agency IT.', '47 placements, 4 call notes'],
    ['Trevor W', 'DTRA DSMS', 'DTRA DSMS', 'DTRA Decision Support & Mission Services', 'GDIT', 'DTRA', '~$200M+', 'Established', 'GDIT Deputy PM mentioned.', '90 call notes'],
    ['Trevor W', 'NTIA FSBS', 'NTIA FSBS', 'NTIA FirstNet/Broadband Support', 'Various', 'NTIA / Commerce', 'Unknown', 'Established', 'Active federal broadband program.', '240 call notes'],

    # CLAY (3 programs - Boeing ESS not Boeing SLS!)
    ['Clay', 'Boeing ESS', 'Boeing ESS', 'Boeing Engineering & Support Services (NOT SLS!)', 'Boeing', 'DoD / NASA', 'Unknown', 'Established', 'CORRECTED: Roster says ESS not SLS. Boeing Engineering & Support Services.', '43 notes for SLS (may overlap)'],
    ['Clay', 'ARCYBER', 'ARCYBER', 'Army Cyber Command', 'Peraton/Various', 'Army', '$1B+', 'Established', 'Peraton-Bob Peters contact. Active pipeline.', '71 placements, 13 call notes'],
    ['Clay', 'NGC LAX', 'NGC LAX', 'Northrop Grumman LAX/El Segundo Programs', 'NGC', 'Various', 'Unknown', 'Established', 'NGC space/IC programs in El Segundo.', '7 call notes'],

    # GEORGE (5 programs - was missing Rattler and IRONHIDE, TITAN X confirmed)
    ['George', 'ISEE', 'ISEE', 'DIA Infrastructure Services Enterprise Engineering', 'GDIT', 'DIA', '$100M', 'Established', '$100M DIA enterprise IT modernization (Oct 2020). Under E-SITE IDIQ.', '36 call notes'],
    ['George', 'NARSIL', 'NARSIL', 'Peraton NARSIL - Advanced System Intelligence', 'Peraton', 'IC', 'Classified', 'Established', 'Classified IC program. Data & Tech Support roles.', '10 placements, 14 call notes'],
    ['George', 'TITAN X', 'TITAN X', 'Air Force Space TITAN X Program', 'AFS', 'Space Force', 'Unknown', 'Established', 'Space Force TITAN satellite/space domain awareness.', 'No Bullhorn data'],
    ['George', 'Rattler', 'RATTLER', 'GDIT Rattler Program', 'GDIT', 'DoD / IC', 'Unknown', 'New Add', 'NEW - Was not in my manual list. GDIT program. Verify.', 'No Bullhorn data'],
    ['George', 'IRONHIDE', 'IRONHIDE', 'GDIT IRONHIDE Program', 'GDIT', 'DoD / IC', 'Unknown', 'Established', 'NEW - Was not in my manual list. GDIT program. Verify.', 'No Bullhorn data'],

    # MATT CAT (8 programs - DOS DJP not BOS SPO, AGUN not AGUNI, TASD not TASKD)
    ['Matt Cat', 'EITaaS', 'EITaaS', 'Enterprise IT as a Service', 'CACI', 'Air Force', '$12.5B IDIQ', 'Established', 'Umbrella for BIM and NaaS. Same vehicle as Colin BIM.', '2 call notes'],
    ['Matt Cat', 'DOS DJP', 'DOS DJP', 'GDIT Dept of State DJP Program (NOT BOS SPO)', 'GDIT', 'State Dept', 'Unknown', 'Established', 'CORRECTED: Roster says DOS DJP not BOS SPO. State Dept IT.', 'No Bullhorn data'],
    ['Matt Cat', 'CITS', 'CITS', 'GDIT Communications & IT Services', 'GDIT', 'Air Force', '~$700M', 'New Add', 'Task Mgr introduction noted. Matches CSV CITS III.', '6 call notes'],
    ['Matt Cat', 'AGUN', 'AGUN', 'Leidos AGUN Program (NOT AGUNI)', 'Leidos', 'Unknown', 'Unknown', 'New Add', 'Roster says AGUN not AGUNI. Verify full name.', 'No Bullhorn data'],
    ['Matt Cat', 'Anduril', 'ANDURIL', 'Anduril Industries Defense Programs (Lattice)', 'Anduril', 'DoD', '$1B+', 'New Add', 'Defense tech (autonomous systems). Active BD.', '53 call notes'],
    ['Matt Cat', 'GPI', 'NGC GPI', 'Northrop Grumman Glide Phase Interceptor', 'NGC', 'MDA', '$4.2B', 'Established', 'GNC Engineer roles. Missile defense hypersonic.', '18 call notes'],
    ['Matt Cat', 'JGLASS II', 'JGLASS II', 'CACI Joint GEOINT Logistics & Analytical Support Svcs II', 'CACI', 'NGA / IC', '~$200M+', 'Established', '5 years remaining. Imagery analyst roles.', '1 call note'],
    ['Matt Cat', 'TASD', 'NGC TASD', 'Northrop Grumman TASD Program (NOT TASKD)', 'NGC', 'DoD', 'Unknown', 'New Add', 'Roster says TASD not TASKD.', 'No Bullhorn data'],

    # ANDY (9 programs - Golden Dome not Golden Base, M2C2 not M22)
    ['Andy', 'Navy QA', 'RTX Navy QA', 'RTX Raytheon Navy Quality Assurance', 'RTX', 'Navy', 'Varies', 'New Add', 'Raytheon Navy weapons systems QA.', 'No Bullhorn data'],
    ['Andy', 'AFS', 'LMCO AFS', 'Lockheed Martin Air Force/Space Programs', 'LMCO', 'AF / Space Force', 'Varies', 'Established', 'Lockheed Martin Air Force Systems.', 'No Bullhorn data'],
    ['Andy', 'Golden Dome', 'RTX Golden Dome', 'RTX Golden Dome Missile Defense Program', 'RTX', 'MDA / DoD', 'Unknown', 'New Add', 'CORRECTED: Roster says Golden Dome not Golden Base. Missile defense initiative.', 'No Bullhorn data'],
    ['Andy', 'FORGE', 'RTX FORGE', 'RTX Raytheon FORGE Program', 'RTX', 'DoD', 'Unknown', 'Established', 'Raytheon program.', '11 call notes'],
    ['Andy', 'M2C2', 'M2C2', 'Multi-domain Mission Command & Control (NOT M22)', 'Unknown', 'Army / DoD', 'Unknown', 'Established', 'CORRECTED: Roster says M2C2 not M22. Multi-domain C2 program.', 'No Bullhorn data'],
    ['Andy', 'Secreps', 'SECREPS', 'Security Representatives Program', 'Various', 'DoD', 'Unknown', 'Established', 'Facility security officer roles.', '10 activities'],
    ['Andy', 'CYBERDYNE', 'CYBERDYNE', 'CYBERDYNE Program', 'Unknown', 'DoD', 'Unknown', 'Established', 'Verify with Andy.', 'No Bullhorn data'],
    ['Andy', 'V-22', 'V-22', 'V-22 Osprey Tiltrotor Aircraft', 'Boeing/Bell', 'Marines / AF', '$40B+ lifecycle', 'Established', 'Osprey sustainment and modernization.', 'No direct Bullhorn data'],
    ['Andy', 'GPS-OCX', 'GPS OCX', 'GPS Operational Control Segment', 'Raytheon', 'Space Force', '$6.2B', 'Established', 'Contact "Carl" offered PM introductions. High-value BD lead.', '2 notes, warm contact'],

    # DREW (8 programs - MRTID not MKID, HMSD not HUSD, IS3 at BAH not RAJ IS2, GMASS confirmed, N2Noms not GINASS, BMC3 not BANC3/W2NLONS)
    ['Drew', 'IBCS', 'IBCS', 'Integrated Battle Command System', 'SAIC', 'Army', '$2.5B+', 'Established', 'Army air/missile defense C2. NGC prime; SAIC support.', '99 notes, 3 placements'],
    ['Drew', 'MRTID', 'SAIC MRTID', 'SAIC MRTID Program (NOT MKID)', 'SAIC', 'DoD', 'Unknown', 'Established', 'CORRECTED: Roster says MRTID not MKID. Verify full name.', 'No Bullhorn data'],
    ['Drew', 'SLEE', 'SAIC SLEE', 'SAIC SLEE Program', 'SAIC', 'Unknown', 'Unknown', 'Established', '7 call notes.', '7 call notes'],
    ['Drew', 'HMSD', 'SAIC HMSD', 'SAIC HMSD Program (NOT HUSD)', 'SAIC', 'DoD', 'Unknown', 'New Add', 'CORRECTED: Roster says HMSD not HUSD.', 'No Bullhorn data'],
    ['Drew', 'IS3', 'BAH IS3', 'Booz Allen Hamilton IS3 Program (NOT RAJ IS2)', 'BAH', 'DoD / IC', 'Unknown', 'Established', 'CORRECTED: Roster says IS3 at BAH (Booz Allen) not RAJ IS2.', 'No Bullhorn data'],
    ['Drew', 'GMASS', 'SAIC GMASS', 'SAIC GMASS Program', 'SAIC', 'DoD', 'Unknown', 'New Add', 'Mentioned in Bullhorn alongside DTAM.', 'Referenced in call notes'],
    ['Drew', 'N2Noms', 'SAIC N2Noms', 'SAIC N2Noms Program (NOT GINASS)', 'SAIC', 'DoD', 'Unknown', 'New Add', 'CORRECTED: Roster says N2Noms. Leidos job #7177 "Netops Admin - N2NOMS" exists in Bullhorn.', '1 placed Bullhorn job (N2NOMS)'],
    ['Drew', 'BMC3', 'SAIC BMC3', 'SAIC Battle Management Command, Control & Communications', 'SAIC', 'DoD', 'Unknown', 'New Add', 'CORRECTED: Roster says BMC3 not BANC3 or W2NLONS. Battle Management C3.', 'No Bullhorn data'],

    # DIAL (4 programs - ADCS not ADCGS)
    ['Dial', 'BIM', 'BIM', 'Base Infrastructure Modernization', 'GDIT', 'Air Force / EITaaS', '$12.5B IDIQ', 'Established', 'Same BIM vehicle as Colin. GDIT awardee.', '3,664 call notes (BIM)'],
    ['Dial', 'DARC', 'NGC DARC', 'Northrop Grumman Deep-space Advanced Radar Capability', 'NGC', 'Space Force / MDA', '$1.4B', 'Established', 'SEIT Manager. In-person meetings. Rate negotiations.', '101 call notes'],
    ['Dial', 'ADCS', 'GDIT ADCS', 'GDIT ADCS Program (roster says ADCS not ADCGS)', 'GDIT', 'Air Force', 'Unknown', 'New Add', 'CORRECTED: Roster says ADCS not ADCGS. Could still be AF DCGS related. Verify.', '71 call notes (DCGS)'],
    ['Dial', 'NGG', 'GDIT NGG', 'GDIT NGG Program', 'GDIT', 'Unknown', 'Unknown', 'New Add', 'Program Director engagement noted.', '99 call notes'],

    # CHAVEZ (4 programs - correct)
    ['Chavez', 'GSMO TN07', 'GSMO TN07', 'DISA GSM-O II Task Number 07', 'Leidos', 'DISA', 'Part of $4.3B GSMO II', 'Established', 'Regional/functional task.', '511 notes, 106 placements (all GSMO)'],
    ['Chavez', 'GSMO TN14', 'GSMO TN14', 'DISA GSM-O II Task Number 14', 'Leidos', 'DISA', 'Part of $4.3B GSMO II', 'Established', 'Regional IT operations.', 'Part of GSMO II'],
    ['Chavez', 'GSMO TN13', 'GSMO TN13', 'DISA GSM-O II Task Number 13', 'Leidos', 'DISA', 'Part of $4.3B GSMO II', 'Established', 'Regional IT operations.', 'Part of GSMO II'],
    ['Chavez', 'GSMO MISC', 'GSMO MISC', 'DISA GSM-O II Miscellaneous/Surge', 'Leidos', 'DISA', 'Part of $4.3B GSMO II', 'Established', 'Surge and misc staffing.', '46 surge placements'],

    # JESSE (6 programs - NCG not NCC/NLC, NG-I not MAR)
    ['Jesse', 'CPS', 'CPS', 'Conventional Prompt Strike (Navy hypersonic)', 'Lockheed Martin', 'Navy', '$1B+', 'Established', 'Navy hypersonic missile program.', '24 notes, 1 placement'],
    ['Jesse', 'NCG', 'NCG', 'NCG Program (NOT NCC or NLC)', 'Unknown', 'Unknown', 'Unknown', 'Established', 'CORRECTED: Roster says NCG. Verify full name.', '1 call note'],
    ['Jesse', 'NG-I', 'NG-I', 'Next Generation Interceptor (NOT MAR)', 'Northrop Grumman', 'MDA', '$13B+', 'Established', 'CORRECTED: Roster says NG-I (Next Gen Interceptor). NGC prime. 13 NGI placements in Bullhorn.', '13 placements (NGI)'],
    ['Jesse', 'GWS', 'GWS', 'GWS Program/Company', 'Unknown', 'Unknown', 'Unknown', 'Established', '1,042 call notes. Appears to be company name. Verify.', '1,042 notes'],
    ['Jesse', 'EREBUS', 'EREBUS', 'EREBUS Program (likely classified)', 'Unknown', 'DoD / IC', 'Unknown', 'Established', 'Very active recruiter engagement.', '342 call notes'],
    ['Jesse', 'NGA Classified', 'NGA Classified', 'NGA Classified Programs', 'Various', 'NGA', 'Classified', 'New Add', 'NGA enterprise IT modernization.', '3 placements'],

    # WILL (8 programs - NCEZID not NXEZIB, SSA ITSSC not OTSSC, CMDP not CANOP)
    ['Will', 'NCEZID', 'NCEZID', 'National Center for Emerging & Zoonotic Infectious Diseases (CDC)', 'Unknown', 'CDC / HHS', 'Unknown', 'Established', 'CORRECTED: Roster says NCEZID (CDC center). NOT NXEZIB.', 'No Bullhorn data'],
    ['Will', 'STOL', 'STOL', 'Short Takeoff and Landing Program', 'Various', 'DoD', 'Unknown', 'Established', 'Aviation defense program.', '7 call notes'],
    ['Will', 'CDC', 'CDC', 'Centers for Disease Control IT Support', 'Leidos', 'HHS / CDC', 'Varies', 'Established', 'Leidos CDC presence.', '1 active job listing'],
    ['Will', 'SSA ITSSC', 'SSA ITSSC', 'Social Security Admin IT Support Services Contract', 'Leidos', 'SSA', '~$1B', 'New Add', 'CORRECTED: Roster says ITSSC not OTSSC. Matches CSV $1.06B Leidos contract.', 'Related to CSV ITSSC'],
    ['Will', 'Leidos SES', 'Leidos SES', 'Leidos Senior Executive/Special Electronic Systems', 'Leidos', 'Unknown', 'Unknown', 'New Add', 'Verify specific division/contract.', 'No Bullhorn data'],
    ['Will', 'Leidos FFSP', 'Leidos FFSP', 'Leidos FFSP Program', 'Leidos', 'Unknown', 'Unknown', 'New Add', 'Verify full name.', 'No Bullhorn data'],
    ['Will', 'GLINDA 2.0', 'GLINDA 2.0', 'GLINDA 2.0 Program (possibly classified)', 'Unknown', 'DoD / IC', 'Unknown', 'New Add', 'Possibly classified IC program.', 'No Bullhorn data'],
    ['Will', 'CMDP', 'CMDP', 'CMDP Program (NOT CANOP)', 'Unknown', 'Unknown', 'Unknown', 'New Add', 'CORRECTED: Roster says CMDP not CANOP. Verify full name.', 'No Bullhorn data'],

    # TANNER (7 programs - NGC IBGS not NGC IBCS, CNPS not CRIPS)
    ['Tanner', 'NGC IBGS', 'NGC IBGS', 'NGC IBGS Program (NOT IBCS)', 'NGC', 'Army / DoD', 'Unknown', 'Established', 'CORRECTED: Roster says IBGS not IBCS. Could be Integrated Battle Ground System variant. 99 IBCS notes may overlap.', '99 notes (IBCS related?)'],
    ['Tanner', 'TALOS', 'TALOS', 'TALOS / Tactical Assault Light Operator Suit', 'Various', 'SOCOM', 'Unknown', 'Established', 'SOCOM special ops tech.', 'No Bullhorn data'],
    ['Tanner', 'AMP', 'AMP', 'AMP Program (LMCO PAC-3 related)', 'Lockheed Martin', 'Army / MDA', 'Unknown', 'Established', 'LMCO PAC-3 production ramp. Missile defense mfg.', '60 call notes'],
    ['Tanner', 'MPACS', 'MPACS', 'Unknown - verify', 'Unknown', 'DoD', 'Unknown', 'New Add', 'Verify full program name.', 'No Bullhorn data'],
    ['Tanner', 'CNPS', 'CNPS', 'CNPS Program (NOT CRIPS)', 'Unknown', 'DoD', 'Unknown', 'New Add', 'CORRECTED: Roster says CNPS not CRIPS. Verify full name.', 'No Bullhorn data'],
    ['Tanner', 'Sentinel', 'SENTINEL', 'Sentinel ICBM (formerly GBSD)', 'Northrop Grumman', 'Air Force', '$95.8B', 'New Add', 'Minuteman III replacement. NGC prime.', '174 call notes'],
    ['Tanner', 'GCCS-J', 'GCCS-J', 'Global Command and Control System - Joint', 'Various', 'DoD', '~$500M', 'New Add', 'Joint C2 system.', '30 activities'],
]

output_path = 'C:/Auto-Claud/Auto-Claude/BD-Automation-Engine/outputs/contract_assignments_CORRECTED.csv'
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow([
        'Person', 'Roster Entry', 'Corrected Acronym', 'Full Program Name',
        'Prime Contractor', 'Agency/Customer', 'Estimated Value', 'Status',
        'Bullhorn Intelligence Summary', 'Bullhorn Data'
    ])
    writer.writerows(rows)

print(f'Written {len(rows)} rows to {output_path}')

# Print corrections summary
print('\n=== KEY CORRECTIONS FROM ROSTER vs MANUAL ENTRY ===')
corrections = [
    ('Colin', 'UNNOD/CENNOD', 'VMOD/GENMOD', 'Completely different programs! VMOD and GENMOD are CACI programs'),
    ('Andres', 'V625B', 'VC25B', 'VC-25B = Air Force One replacement (Boeing)'),
    ('Andres', 'BA + Cruise Mint', 'DA & Cruise Missiles', 'Defense/Attack & Cruise Missiles'),
    ('Steph', 'Hub Central', 'HUD Central', 'HUD (Housing & Urban Development) not Hub'),
    ('Steph', 'GDIT DCGS', 'DEOS', 'COMPLETELY DIFFERENT! DEOS = Defense Enterprise Office Solutions (DOD365), NOT DCGS'),
    ('Steph', 'TRX ANR XRYA-2', 'ANTYPY-2', 'Different program name entirely'),
    ('Steph', 'FAA NISCIV', 'FAA MISCIV', 'MISCIV not NISCIV'),
    ('Logan', 'Deloitte ACC', 'ARC (Deloitte)', 'ARC not ACC'),
    ('Logan', 'Navy FPIV', 'NAVY FIP IV', 'FIP IV not FPIV'),
    ('Logan', 'JSFACS', 'JSFACE', 'JSFACE not JSFACS'),
    ('Emily/Hoppe', 'Emily', 'Hoppe', 'Person name is Hoppe not Emily'),
    ('IDK', 'NTT NAIS', 'NTT NNIS', 'NNIS not NAIS'),
    ('IDK', 'PERATON BECO/DECO', 'Peraton DCLO', 'DCLO not BECO or DECO'),
    ('Emma', 'GSMO TN15', 'GSMO TNIS', 'TNIS not TN15 (but likely TN15 or TN1S)'),
    ('Emma', 'GSMO TN0 EMORY', 'GSMO TNO1 + Emory Uni', 'Two separate entries: TNO1 and Emory Uni'),
    ('Trevor W', '(missing)', 'NISST', 'New program not in manual list'),
    ('Clay', 'BOEING SLS', 'Boeing ESS', 'ESS (Engineering Support Services) NOT SLS (Space Launch System)!'),
    ('George', '(missing)', 'Rattler + IRONHIDE', 'Two GDIT programs missing from manual list'),
    ('Matt Cat', 'GDIT BOS SPO', 'DOS DJP', 'State Dept program, NOT base operations'),
    ('Matt Cat', 'LEIDOS AGUNI', 'AGUN', 'AGUN not AGUNI'),
    ('Matt Cat', 'NGC TASKD', 'TASD', 'TASD not TASKD'),
    ('Andy', 'RTX GOLDEN BASE', 'RTX Golden Dome', 'Golden DOME not Golden BASE (missile defense)'),
    ('Andy', 'M22', 'M2C2', 'Multi-domain Mission C2, not M22'),
    ('Drew', 'SAIC MKID', 'MRTID', 'MRTID not MKID'),
    ('Drew', 'SAIC HUSD', 'HMSD', 'HMSD not HUSD'),
    ('Drew', 'RAJ IS2', 'IS3 (BAH)', 'IS3 at Booz Allen Hamilton, not RAJ IS2'),
    ('Drew', 'SAIC GINASS', 'GMASS', 'GMASS not GINASS'),
    ('Drew', 'SAIC BANC3 / W2NLONS', 'BMC3 / N2Noms', 'Two separate programs: BMC3 and N2Noms'),
    ('Dial', 'GDIT ADCGS', 'ADCS', 'ADCS not ADCGS'),
    ('Jesse', 'NCC or NLC', 'NCG', 'NCG not NCC/NLC'),
    ('Jesse', 'MAR', 'NG-I', 'Next Generation Interceptor, not MAR'),
    ('Will', 'NXEZIB', 'NCEZID', 'CDC National Center for Emerging & Zoonotic Infectious Diseases'),
    ('Will', 'SSA OTSSC', 'SSA ITSSC', 'ITSSC not OTSSC'),
    ('Will', 'CANOP', 'CMDP', 'CMDP not CANOP'),
    ('Tanner', 'NGC IBCS', 'NGC IBGS', 'IBGS not IBCS'),
    ('Tanner', 'CRIPS', 'CNPS', 'CNPS not CRIPS'),
]

for person, wrong, right, note in corrections:
    print(f'  {person}: "{wrong}" -> "{right}" ({note})')
