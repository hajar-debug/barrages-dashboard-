with tab4:
        st.markdown("### 📄 Analyse Hydrologique & Rapport")
        interpretation = ""
        if ndwi is not None:
            if ndwi > 0.15: 
                interpretation += "✅ **État de l'eau** : Remplissage élevé.\n\n"
            elif ndwi > 0.02:
                interpretation += "⚠️ **État de l'eau** : Niveau moyen.\n\n"
            else:
                interpretation += "🚨 **Alerte** : Sécheresse critique.\n\n"

        if st.button("🏗️ Préparer le rapport PDF"):
            with st.spinner("Génération..."):
                pdf_output = generate_pdf(choice, row, ndwi, ndvi, water, rl, rs, al, start_str, end_str, ndti, fig=fig)
                try:
                    if hasattr(pdf_output, 'output'):
                        pdf_bytes = pdf_output.output(dest='S')
                    elif isinstance(pdf_output, str):
                        pdf_bytes = pdf_output.encode('latin-1')
                    else:
                        pdf_bytes = pdf_output
                except Exception as e:
                    st.error(f"Erreur conversion : {e}")
                    pdf_bytes = None

                if pdf_bytes:
                    st.success("✅ Rapport prêt !")
                    st.download_button(label="📥 Télécharger PDF", data=pdf_bytes, file_name=f"Rapport_{choice}.pdf", mime="application/pdf")
        
        st.info(interpretation if interpretation else "Sélectionnez une période.")