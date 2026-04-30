# PCR Prep

### Author
[Opentrons](https://opentrons.com/)



## Categories
* PCR
	* PCR Prep

## Description

Links:
* [Random Aliquoting](./925d07-cp)
<br></br>
<br></br>
* [Plasmind Luciferase Assay](./925d07-pla)
<br></br>
<br></br>
* [QIAcuity Plate Transfer](./925d07-q)
<br></br>
<br></br>
* [PCR Prep](./925d07-v3)
<br></br>
<br></br>

This protocol performs a custom PCR prep from 4 source 96-well RNA plate to a single 384-well destination plate. The transfer scheme is shown below.

---

### Labware
* [Opentrons 20ul tips](https://shop.opentrons.com/collections/opentrons-tips)
* Corning 96 Well Plate 360 ul Flat
* Custom 384 Well Plate 100 ul
* Generic PCR Strips in [96-well aluminum block](https://shop.opentrons.com/collections/hardware-modules/products/aluminum-block-set)

### Pipettes
* [P20 Multi Channel Pipette](https://shop.opentrons.com/collections/ot-2-robot/products/8-channel-electronic-pipette)

### Modules
* [Temperature Module GEN2](https://shop.opentrons.com/collections/hardware-modules/products/tempdeck)

---

### Deck Setup
![deck layout](https://opentrons-protocol-library-website.s3.us-east-1.amazonaws.com/custom-README-images/925d07/deck.png?versionId=qLdqfwXnxAUL.Q0DsCMwQD4t37oqX96S&response-content-disposition=inline&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEHkaCXVzLWVhc3QtMiJIMEYCIQDh2SuhUJrAbGVRHxOnqIYvsuoX24YLUMskYfu4dDbVDQIhAN7JMJvSaDkV8ahLnkw1%2FxG2YmkjtwszFEmpJ7nm6M3QKogDCJL%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEQAxoMNDgwMDM0NzU4NjkxIgwP%2F8LEp6TeMPVl7Pgq3ALlyIR0p8yxAJOfNvoGleOs1edmgGEByFqDf0VYNkqBGMarkQZNcYqipaQxF82afh5lA2ck4RXMPj9xRq%2FKTHAE0xigIYUkGOJgqjxkilNgCakvGI4ILdjzEjIKuuDYMwfHdR7VS%2BuADUjTY9ZvpeQkktrsMzwgD%2BLk9hcMbkRWNWPea3AlmgNAgoq%2BSLbIMFHtd99DTf8N1OKqum6omteVXWoTWH0hUXMeLZyQ9gQZZ0%2F22e8Mh3DRE3%2FdLjh92m%2Brm8o1TKBMB0hPDrCv1zKm2%2BCSAuHoxODgb4W0RyEBiJGwH%2Be%2F1ZLu%2FnYsrLC0UGXZsArBYSosyszPchnlnSrguA%2F5p%2FKW0yWb%2FL%2Bkqcg%2F%2F%2F4%2Bh5iZ1SycKFvgMC7Ma%2Bcp6IBOozTpLVBeU6jEP1VeIEAeBxNF0QmUeiUwDQ3OIH0bKBQlOdOdbc0qHgD9u9nEvTv877odHjbVhxowmuPXlQY6sgLOeJ6t17RfHSgszFXMyppkhwCibNOx3c26ou3XM%2Fretauca%2BKovLWZlRtPrggxliFJeVUlXqV7k3dpC4XhwJeuybmcA8FaPvz%2FsHKm0zmLRpqmpp438rs8AXDuJNbp%2BHoPhTcc4AjAfq0xyrhY07VU%2FAAn0B2%2FdwDB1cuRrf4rt4iQeeFhGuC8AuMVnOcVAW2ORvqll067lcYUyWLzt5Nit7ncgG1V9tgKA0bZ2ZEIxciJRbMhmYtj%2BqwgxVymSmeb11q6LJMH0acrJTnXJJYiWHZ%2BAFPXDHN%2FKhLimqc9OPDJs9n8BwXZsJ78K0Hwk6u1HBm1grrKHyrPT%2F4gNcCUG0%2Bpc6Eh6ZS9JrPvq3KAy8%2F1jKrHFhNnLoCsQAhnt8tvWtoQCFWC4jXDEMCDwf2ZtZM%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20220624T172242Z&X-Amz-SignedHeaders=host&X-Amz-Expires=300&X-Amz-Credential=ASIAW7RCNEARRJXZPZ64%2F20220624%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=6b9bc0f27c223ed652b90a98e00fb9172f72b014445bdcdd94899779d50109d3)

---

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
9250d7
