 name: Run script to fetch and append new data
        run: |
          python fetch_and_append_bls_data.py  # Your Python script
        env:
          BLS_API_KEY: ${{ secrets.BLS_API_KEY }}  # Pass API key from GitHub secrets

      - name: Commit and push changes
        run: |
          git config --global user.name "Your GitHub Username"
          git config --global user.email "Your Email"
          git add bls_data.csv
          git commit -m "Update BLS data"
          git push
          git push origin main  # Ensure you're pushing to the correct branch
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}  # Use GitHub's token for authentication
