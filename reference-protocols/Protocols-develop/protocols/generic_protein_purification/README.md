# Generic Protein Purification Protocol

### Author
[Opentrons](https://opentrons.com/)



## Categories
* Protein Purification
    * Generic Protein Purification

## Description

The generic protein purification is a flexible protocol that starts from bacterial
media ready for lysis on a well plate. From there the protocol adds lysis buffer
and then proceeds to bind the target his-tagged proteins with nickel linked paramagnetic beads. After a variable amount of washes the user may choose to
elute the proteins using elution buffer, or with SDS buffer if the purpose is to
run the samples on a gel.

The user is given extensive control of the protocol from the parameters. Pipettes, labware, modules (i.e. temperature and magnetic modules), protocol steps, and volumes are examples of things that can be customized to the users specifications.

The protocol is based on Promega's MagneHis™ system, but should work for any other similar system.

**Parameters**

* `Magnet engagment time for bead binding` How long to engage magnets in order to attract the beads before doing any pipetting steps
* `Number of samples` How many bacterial media samples there are on the sample plate
* `Small pipette` The smaller pipette, can be a multi-channel or single
* `Large pipette`The larger pipette, can be a multi-channel or single
* `Small pipette tip-racks` Tips to use with the small pipette
* `Large pipette tip-racks` Tips to use with the large pipette
* `Reagent reservoir` 12 well reservoir for reagents: Lysis buffer, NaCl (optional), Wash buffer, elution buffer, SDS buffer (optional), paramegnetic beads.
* `Destination plate` Plate where eluted proteins are transferred after adding elution or SDS buffer
* `Sample plate` Plate containing wells with bacterial media
* `Magnetic module` Which magnetic module to use for the bead binding steps
* `Tube rack (optional)` Tube rack for DNAse I (well 1) if used.
* `Destination plate temperature module (optional)` A temperature module for controlling the temperature of the destination plate
* `Pause robot operation to allow user to vortex magnetic beads?` If this parameter is on, the robot will pause before the paramagnetic bead addition step to allow the user to resuspend the beads by vortexing the solution before adding it to the reservoir.
* `Elute proteins in SDS buffer instead of elution buffer` Allows the user to elute proteins with SDS buffer instead of elution buffer if the proteins are intended to be run on a gel
* `Add DNAse I to lysis sample from a tube?` If yes, then DNAse will be added from well A1 of the (optional) tube rack. If no, then the DNAse should be added to the lysis buffer in the reservoir prior to running the protocol
* `Add NaCl to samples to a conc. of 500 mM during wash steps to enhance protein binding?` Optional; If you want to do this step, Add a 4M NaCl solution to the reservoir (see picture in the deck setup section)
* `Volume of paramagnetic beads to use with each sample (µL)` Volume of paramagnetic beads to add to each sample well after the lysis step
* `Initial volume (of bacteria containing media in each sample well) (µL)` Initial volume of sample in each sample plate well containing bacterial culture to be lysed.
* `Wash buffer volume for the washing steps (µL)` Volume of wash buffer to use in each washing step
* `Elution buffer volume to elute proteins with (µL)` How much elution buffer to elute the purified protein with.
* `Number of washing steps` How many repetitions of washing the beads to remove unwanted proteins and other contaminants.
* `Number of times to mix the wash buffer with the beads for each wash step` Number of times to mix (pipette solution up and down) for each washing step in order to mix the solution.
* `Number of times to mix the elution buffer with the beads` Number of times to mix the elution buffer with the samples before transferring the protein containing supernatant.
* `Bead incubation time for binding and eluting protein (before magnets are engaged)` How many minutes to incubate beads with the lysed bacterial solution before engaging magnets, also the amount of time to incubate the beads with elution buffer before engaging magnets.
* `Number of times to mix the bead solution before transferring beads to the samples` Optional number of times to use the large pipette to mix the bead solution before transferring the bead solution to the samples
* `SDS buffer volume to elute proteins with (optional: this only matters if you decide to elute with SDS buffer)` In the final step you can choose whether to elute with elution buffer or SDS buffer if you want to run a gel on the samples, this parameter specifies the volume in microliter of SDS buffer.

---

### Modules
* [Temperature Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)
* [Magnetic Module (GEN2)](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)

### Labware
* [12-well Reservoirs](https://labware.opentrons.com/?category=reservoir)
	* [NEST 12 well reservoir, 15 mL](https://shop.opentrons.com/nest-12-well-reservoirs-15-ml/)
* [Well plates](https://labware.opentrons.com/?category=wellPlate)
	* [NEST 2 mL 96-Well Deep Well Plate](https://shop.opentrons.com/nest-2-ml-96-well-deep-well-plate-v-bottom/)
* [Target plate](https://labware.opentrons.com/?category=wellPlate)
	* [NEST 96 Well Plate Flat](https://shop.opentrons.com/nest-96-well-plate-flat/)
* [Tube racks](https://labware.opentrons.com/?category=tubeRack)
	* [4-in-1 Tube Rack Set](https://shop.opentrons.com/4-in-1-tube-rack-set/)

### Pipettes
* [Opentrons Pipettes](https://opentrons.com/pipettes/)

### Reagents
Protein purification kit with paramagnetic beads, for example: [MagneHis™ Protein Purification System](https://www.promega.com/products/protein-purification/protein-purification-kits/magnehis-protein-purification-system/?catNum=V8500#protocols)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/generic_protein_purification/deck.jpg)

### Reagent Setup
![Reagent reservoir](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/generic_protein_purification/liquids.jpg)

---

### Protocol Steps
The protocol is based on [MagneHis protein purification protocol](https://www.promega.com/-/media/files/resources/protocols/technical-manuals/0/magnehis-protein-purification-system-protocol.pdf?rev=cbf49f7cf6fa4696b965c92c1f8e9c72&sc_lang=en), however a similar kit should work as well.
1. Bacterial lysis: Lysis buffer is added to all the sample wells. If the DNAse step is activated DNAse will be added to each well as well (see parameter options below). If it's not activated DNAse I should be added to the lysis buffer by the user before running the protocol (1 µL per mL of bacterial media to lyse)
2. The protocol is paused to allow the user to shake the sample plate for 10-20 minutes at room temperature for the lysis reaction to complete
3. Binding: The paramagnetic beads are added to the samples, along with sodium chloride, if desired. The user has an option to pause the protocol before this step in order to vortex the beads in order to resuspend them. The user may also specify a number of mixes with the pipettes to help homogenize the solution.
4. The beads are washed with wash buffer (and optionally NaCl) and the supernatant is removed while the magnets on the magnetic module are engaged. This is repeated as many times as the user wants.
5. Elution: Finally the wash supernatant is removed while the magnets are engaged and elution buffer (or optionally: SDS buffer replaces the EB if the user desires to run the samples on a gel) is added. The bead supernatant is transferred to the target plate.

### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
generic_protein_purification
