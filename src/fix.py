import pikepdf

pdf = pikepdf.open("data/infosys_2024_25.pdf")
pdf.save("data/infosys_2024_25_repaired.pdf")
pdf.close()

print("Repaired copy saved.")