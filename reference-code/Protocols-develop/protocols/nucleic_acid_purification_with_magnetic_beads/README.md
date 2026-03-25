# Nucleic Acid Purification with Magnetic Beads

### Author
[Opentrons](https://opentrons.com/)


## Categories
* Featured
    * Nucleic Acid Purification with Magnetic Beads (Universal)

## Description
With this protocol, you can perform high-quality nucleic acid purifications using magnetic beads and the [Opentrons Magnetic Module](https://shop.opentrons.com/products/magdeck]). This protocol contains flexible parameters that you can customize for many different magnetic bead and nucleic acid types. Use this setup to rapidly iterate and optimize your magbead-based workflows!

You can use any magnetic beads you prefer with this protocol, but we have included some reagent recommendations in the **Materials Needed** section below to help you get started. For more detailed information on how to use this protocol, please see our [Technical Note](https://s3.amazonaws.com/opentrons-protocol-library-website/Technical+Notes/Nucleic+Acid+Purification+with+Magnetic+Module+OT2+Technical+Note.pdf).

---

---

![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/customizable-serial-dilution/materials.png)

-- [Opentrons OT-2](http://opentrons.com/ot-2)

-- [Opentrons Magnetic Module](https://shop.opentrons.com/products/magdeck?_ga=2.171718441.823190023.1542396855-403439593.1535387376)

-- [Opentrons OT-2 Run App (Version 3.1.2 or later)](http://opentrons.com/ot-app)

-- 200uL or 300 uL Tiprack ([Opentrons tips suggested](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips-racks-9-600-tips))

-- [12-row automation-friendly trough](https://www.usascientific.com/12-channel-automation-reservoir.aspx)

-- [BioRad HardShell 96-Well PCR Plate](http://www.bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)

-- Magnetic Beads (Looking for a kit? We recommend trying [Omega Bio-tek Mag-Bind® TotalPure NGS](https://shop.opentrons.com/products/mag-bind-total-pure-ngs))

-- Ethanol

-- Elution Buffer (Typically 10 mM Tris pH 8.0, TE Buffer, or nuclease-free water)

---

---

![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Using the customization fields below, set up your protocol as follows:

   * **Pipette:** Specify your pipette. We recommend using a p50 or p300 multi- or single-channel.
   * **Pipette Mount:** Specify which mount (left or right) your pipette is on.
   * **Sample number:** Customize the number of samples to run per protocol. A multiple of 8 is recommended when you are using a multichannel pipette.
   * **Sample volume:** Specify the starting volume (in uL) of the input sample.
   * **Bead Ratio:** Customize the ratio of beads for left or right side size-selection of fragments. *The default bead ratio is 1.8x the input sample volume.*
   * **Elution Volume:** Specify the final volume (in uL) to elute the purified nucleic acid. *The Opentrons MagDeck supports elution volumes above 10 µL.*
   * **Incubation Time:** Specify the amount of time (in minutes) that the bead solution and input sample interact.
   * **Settling Time:** Specify the amount of time (in minutes) needed to pellet the beads. *Higher volumes may require a longer settling time.*
   * **Drying Time:** Specify the drying time (in minutes) needed after wash steps.

---

---

## Process
1. Select all desired settings according to the "Setup" section above to create your customized protocol.
2. Download your customized Nucleic Acid Purification protocol using the blue "Download" button.
3. Upload your protocol file into the Opentrons Run App and follow the instructions there to set up your deck and proceed to run.
4. Make sure to add reagents to your labware before placing it on the deck! You can see where to place your reagents below.

![Labware setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/Nucleic+Acid+Purification/Nucleic+Acid+Purification+with+Magnetic+Beads+-+Reagent+Start+Position.png)

###### Internal
Nucleic Acid Purification, v1

### Additional Notes
Please reference our [Technical Note](https://s3.amazonaws.com/opentrons-protocol-library-website/Technical+Notes/Nucleic+Acid+Purification+with+Magnetic+Module+OT2+Technical+Note.pdf) for more information about the expected output of this protocol, in addition to expanded sample data from the Opentrons lab.

We understand that there are limitations to the use of this protocol and we plan to make improvements soon! In the meantime, if you'd like to request a more complex purification workflow, please use our [Protocol Development Request Form](https://opentrons-protocol-dev.paperform.co/). You can also download the Python file from this page and modify it using our [API Documentation](https://docs.opentrons.com/). For additional questions about this protocol, please email <protocols@opentrons.com>.

## Preview
Perform high-quality nucleic acid purifications using any magnetic beads and the [Opentrons Magnetic Module](https://shop.opentrons.com/products/magdeck]).
