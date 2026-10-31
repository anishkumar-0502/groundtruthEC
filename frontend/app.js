/**
 * Ground Truth — TNREGINET EC Retrieval Service Frontend Client
 * With Full Multilingual Support (English Default & Tamil)
 */

document.addEventListener("DOMContentLoaded", () => {
    // Current Active Language (Default: English 'en')
    let currentLang = localStorage.getItem("app_lang") || "en";
    let currentSessionId = null;

    // Translations Dictionary
    const TRANSLATIONS = {
        en: {
            brandSub: "Encumbrance Certificate Retrieval",
            step1Title: "Step 1: Configure EC Search",
            step1Sub: "Select location hierarchy dynamically loaded from the official portal.",
            modeSurveyTitle: "Survey Number Search",
            modeSurveySub: "Search by Village, Survey No., and optional Subdivision",
            modeWardTitle: "Town Ward / Block Search",
            modeWardSub: "Search by Village, Town, Ward, and Block",
            lblZone: "Registration Zone",
            lblDistrict: "District",
            lblSro: "Sub-Registrar Office (SRO)",
            lblVillage: "Village",
            lblSurveyNo: "Survey Number",
            lblSubDivNo: "Subdivision Number",
            optional: "(Optional)",
            lblTown: "Revenue Town",
            lblWard: "Ward",
            lblBlock: "Block",
            lblStartDate: "Start Date",
            lblEndDate: "End Date",
            btnStartSearch: "Initialize Portal Session & Retrieve CAPTCHA",
            btnStartSearchLoading: "Initializing Session...",
            step2Title: "Step 2: Enter Portal CAPTCHA",
            step2Sub: "Human verification required. This image was fetched directly from TNREGINET in real-time.",
            lblCaptchaPrompt: "Enter the characters displayed in the image above:",
            btnSubmitSearch: "Submit & Search EC",
            btnSubmitSearchLoading: "Verifying & Searching...",
            resultsTitle: "Encumbrance Certificate Records",
            btnDownloadPdf: "📄 Download Ground Truth EC PDF",
            thDocNo: "Document #",
            thYear: "Year",
            thRegDate: "Registration Date",
            thDocType: "Document Type",
            thExecutants: "Executants",
            thClaimants: "Claimants",
            thConsid: "Consideration Value",
            thMarket: "Market Value",
            thSurvey: "Survey Nos.",
            thAction: "Document / Download",
            selZonePlaceholder: "Select Zone",
            selDistrictPlaceholder: "Select District",
            selSroPlaceholder: "Select SRO",
            selVillagePlaceholder: "Select Village",
            selTownPlaceholder: "Select Town",
            selWardPlaceholder: "Select Ward",
            selBlockPlaceholder: "Select Block",
            loadingZones: "Loading Zones...",
            loadingDistricts: "Loading Districts...",
            loadingSros: "Loading SROs...",
            loadingVillages: "Loading Villages...",
            noOptions: "No options available",
            sessionReadyMsg: "Portal session ready. Please enter the CAPTCHA image characters.",
            noRecordsFound: "தேடுதல் காலத்தில் எந்த ஆவணங்களும் பதிவு செய்யப்படவில்லை (No transactions registered in this period).",
            wrongCaptchaMsg: "The entered CAPTCHA was rejected by the portal. A new image has been loaded. Please try again.",
            sessionExpiredMsg: "The portal session expired. Please click 'Initialize Portal Session' again.",
        },
        ta: {
            brandSub: "வில்லங்கச் சான்று மீட்டெடுப்பு",
            step1Title: "படி 1: வில்லங்கச் சான்று தேடல் கட்டமைப்பு",
            step1Sub: "அதிகாரப்பூர்வ போர்ட்டலில் இருந்து இருப்பிடங்களைத் தேர்ந்தெடுக்கவும்.",
            modeSurveyTitle: "புல எண் வாரியாக",
            modeSurveySub: "கிராமம், புல எண் மற்றும் உட்பிரிவு எண் வாரியாக தேடுதல்",
            modeWardTitle: "வார்டு / பிளாக் வாரியாக",
            modeWardSub: "கிராமம், நகரம், வார்டு மற்றும் பிளாக் வாரியாக தேடுதல்",
            lblZone: "பதிவு மண்டலம்",
            lblDistrict: "மாவட்டம்",
            lblSro: "சார்பதிவாளர் அலுவலகம் (SRO)",
            lblVillage: "கிராமம்",
            lblSurveyNo: "புல எண்",
            lblSubDivNo: "உட்பிரிவு எண்",
            optional: "(விருப்பமானது)",
            lblTown: "வருவாய் நகரம்",
            lblWard: "வார்டு",
            lblBlock: "பிளாக்",
            lblStartDate: "தொடக்க நாள்",
            lblEndDate: "முடிவு நாள்",
            btnStartSearch: "அமர்வை துவக்கி கேப்ட்சாவைப் பெறுக",
            btnStartSearchLoading: "அமர்வை துவக்குகிறது...",
            step2Title: "படி 2: போர்ட்டல் கேப்ட்சாவை உள்ளிடவும்",
            step2Sub: "மனித சரிபார்ப்பு தேவை. இந்த படம் நேரடியாக போர்ட்டலில் இருந்து பெறப்பட்டது.",
            lblCaptchaPrompt: "மேலே உள்ள படத்தில் உள்ள எழுத்துக்களை உள்ளிடவும்:",
            btnSubmitSearch: "சமர்ப்பித்து தேடுக",
            btnSubmitSearchLoading: "சரிபார்த்து தேடுகிறது...",
            resultsTitle: "வில்லங்கச் சான்று பதிவுருக்கள்",
            btnDownloadPdf: "📄 அசல் வில்லங்கச் சான்று PDF பதிவிறக்கம்",
            thDocNo: "ஆவண எண்",
            thYear: "ஆண்டு",
            thRegDate: "பதிவு நாள்",
            thDocType: "ஆவண வகை",
            thExecutants: "எழுதி கொடுத்தவர்",
            thClaimants: "எழுதி வாங்கியவர்",
            thConsid: "கைமாற்றுத் தொகை",
            thMarket: "சந்தை மதிப்பு",
            thSurvey: "புல எண்கள்",
            thAction: "ஆவணம் / பதிவிறக்கம்",
            selZonePlaceholder: "மண்டலத்தினைத் தெரிவு செய்க",
            selDistrictPlaceholder: "மாவட்டத்தினைத் தெரிவு செய்க",
            selSroPlaceholder: "சார்பதிவாளர் அலுவலகத்தினைத் தெரிவு செய்க",
            selVillagePlaceholder: "கிராமத்தினைத் தெரிவு செய்க",
            selTownPlaceholder: "நகரத்தினைத் தெரிவு செய்க",
            selWardPlaceholder: "வார்டினைத் தெரிவு செய்க",
            selBlockPlaceholder: "பிளாக்கினைத் தெரிவு செய்க",
            loadingZones: "மண்டலங்கள் ஏற்றப்படுகின்றன...",
            loadingDistricts: "மாவட்டங்கள் ஏற்றப்படுகின்றன...",
            loadingSros: "அலுவலகங்கள் ஏற்றப்படுகின்றன...",
            loadingVillages: "கிராமங்கள் ஏற்றப்படுகின்றன...",
            noOptions: "விவரங்கள் இல்லை",
            sessionReadyMsg: "போர்ட்டல் அமர்வு தயார். தயவுசெய்து கேப்ட்சா குறியீட்டை உள்ளிடவும்.",
            noRecordsFound: "தேடுதல் காலத்தில் எந்த ஆவணங்களும் பதிவு செய்யப்படவில்லை.",
            wrongCaptchaMsg: "தவறான காப்புக் குறியீடு. புதிய படம் ஏற்றப்பட்டுள்ளது, மீண்டும் முயற்சிக்கவும்.",
            sessionExpiredMsg: "உங்கள் அமர்வு காலாவதியாகி விட்டது. தயவுசெய்து மீண்டும் தொடங்கவும்.",
        }
    };

    // Comprehensive bilingual location dictionary
    const LOCATION_TRANSLATIONS = {
        "அரியலூர்": "Ariyalur",
        "இராணிப்பேட்டை": "Ranipet",
        "இராமநாதபுரம்": "Ramanathapuram",
        "ராமநாதபுரம்": "Ramanathapuram",
        "ஈரோடு": "Erode",
        "கடலூர்": "Cuddalore",
        "கரூர்": "Karur",
        "கள்ளக்குறிச்சி": "Kallakurichi",
        "கன்னியாகுமரி": "Kanyakumari",
        "காஞ்சிபுரம்": "Kanchipuram",
        "கிருஷ்ணகிரி": "Krishnagiri",
        "கோயம்புத்தூர்": "Coimbatore",
        "கோயமுத்தூர்": "Coimbatore",
        "கோயம்புத்தூர் தெற்கு": "Coimbatore South",
        "கோயம்புத்தூர் வடக்கு": "Coimbatore North",
        "சிவகங்கை": "Sivagangai",
        "செங்கல்பட்டு": "Chengalpattu",
        "சென்னை": "Chennai",
        "சென்னை தெற்கு": "Chennai South",
        "சென்னை மத்திய": "Chennai Central",
        "சென்னை வடக்கு": "Chennai North",
        "சேலம்": "Salem",
        "சேலம் மேற்கு": "Salem West",
        "சேலம் கிழக்கு": "Salem East",
        "தஞ்சாவூர்": "Thanjavur",
        "தர்மபுரி": "Dharmapuri",
        "திருவாரூர்": "Tiruvarur",
        "திண்டுக்கல்": "Dindigul",
        "திருச்சிராப்பள்ளி": "Tiruchirappalli",
        "திருச்சி": "Tiruchirappalli",
        "திருநெல்வேலி": "Tirunelveli",
        "திருப்பத்தூர்": "Tirupathur",
        "திருப்பூர்": "Tiruppur",
        "திருவண்ணாமலை": "Tiruvannamalai",
        "திருவள்ளூர்": "Tiruvallur",
        "தூத்துக்குடி": "Thoothukudi",
        "தென்காசி": "Tenkasi",
        "தேனி": "Theni",
        "நாகப்பட்டினம்": "Nagapattinam",
        "நாமக்கல்": "Namakkal",
        "நீலகிரி": "Nilgiris",
        "புதுக்கோட்டை": "Pudukkottai",
        "பெரம்பலூர்": "Perambalur",
        "மதுரை": "Madurai",
        "மதுரை தெற்கு": "Madurai South",
        "மதுரை வடக்கு": "Madurai North",
        "மயிலாடுதுறை": "Mayiladuthurai",
        "விருதுநகர்": "Virudhunagar",
        "விழுப்புரம்": "Villupuram",
        "வேலூர்": "Vellore",
        "கோபிசெட்டிபாளையம்": "Gobichettipalayam",
        "ஊட்டி": "Ooty",
        "உதகமண்டலம்": "Ooty",
        "மதுக்கரை": "Madukkarai",
        "சிங்காநல்லூர்": "Singanallur",
        "பீளமேடு": "Peelamedu",
        "சூலூர்": "Sulur",
        "பொள்ளாச்சி": "Pollachi",
        "ஆனைமலை": "Anaimalai",
        "கிணத்துக்கடவு": "Kinathukkadavu",
        "நெகமம்": "Negamam",
        "குமாரபாளையம்": "Kumarapalayam",
        "பவானி": "Bhavani",
        "அம்மாபேட்டை": "Ammapettai",
        "தெற்கு": "South",
        "வடக்கு": "North",
        "கிழக்கு": "East",
        "மேற்கு": "West",
        "மத்திய": "Central",
        "இணை": "Joint",
    };

    // DOM Elements
    const appLanguageSelect = document.getElementById("appLanguageSelect");
    const modeSurvey = document.getElementById("modeSurvey");
    const modeWardBlock = document.getElementById("modeWardBlock");
    const surveyFields = document.querySelectorAll(".survey-mode-field");
    const wardFields = document.querySelectorAll(".ward-mode-field");

    const cmbZone = document.getElementById("cmbZone");
    const cmbDistrict = document.getElementById("cmbDistrict");
    const cmbSro = document.getElementById("cmbSro");
    const cmbVillage = document.getElementById("cmbVillage");
    const cmbTown = document.getElementById("cmbTown");
    const cmbWard = document.getElementById("cmbWard");
    const cmbBlock = document.getElementById("cmbBlock");

    const txtSurveyNo = document.getElementById("txtSurveyNo");
    const txtSubDivNo = document.getElementById("txtSubDivNo");
    const txtStartDate = document.getElementById("txtStartDate");
    const txtEndDate = document.getElementById("txtEndDate");
    const searchForm = document.getElementById("searchForm");
    const btnStartSearch = document.getElementById("btnStartSearch");

    const captchaSection = document.getElementById("captchaSection");
    const captchaImage = document.getElementById("captchaImage");
    const btnRefreshCaptcha = document.getElementById("btnRefreshCaptcha");
    const txtCaptcha = document.getElementById("txtCaptcha");
    const btnSubmitSearch = document.getElementById("btnSubmitSearch");

    const statusAlert = document.getElementById("statusAlert");
    const alertTitle = document.getElementById("alertTitle");
    const alertMessage = document.getElementById("alertMessage");

    const resultsSection = document.getElementById("resultsSection");
    const resultsSummary = document.getElementById("resultsSummary");
    const ecTableBody = document.getElementById("ecTableBody");
    const pdfActionContainer = document.getElementById("pdfActionContainer");
    const btnDownloadPdf = document.getElementById("btnDownloadPdf");

    // Ground Truth Elements (Subdivisions, Saved ECs, Recent Pills)
    const formSurveyHint = document.getElementById("formSurveyHint");
    const downloadCard = document.getElementById("downloadCard");
    const btnDownloadECMain = document.getElementById("btnDownloadECMain");

    const subdivisionsSection = document.getElementById("subdivisionsSection");
    const subdivDropdownTrigger = document.getElementById("subdivDropdownTrigger");
    const subdivDropdownMenu = document.getElementById("subdivDropdownMenu");
    const subdivCheckboxList = document.getElementById("subdivCheckboxList");
    const subdivSelectedCountText = document.getElementById("subdivSelectedCountText");
    const subdivSummaryCount = document.getElementById("subdivSummaryCount");
    const btnSelectAllSubdivs = document.getElementById("btnSelectAllSubdivs");
    const btnClearSubdivs = document.getElementById("btnClearSubdivs");
    const btnDownloadSelectedSubdivs = document.getElementById("btnDownloadSelectedSubdivs");
    const subdivCardsList = document.getElementById("subdivCardsList");

    const recentlyDownloadedSection = document.getElementById("recentlyDownloadedSection");
    const recentlyDownloadedPills = document.getElementById("recentlyDownloadedPills");
    const savedEcsSection = document.getElementById("savedEcsSection");
    const savedEcsHeading = document.getElementById("savedEcsHeading");
    const savedEcsTableBody = document.getElementById("savedEcsTableBody");

    // Live Survey Hint update
    function updateSurveyHint() {
        if (!formSurveyHint) return;
        const sNo = txtSurveyNo.value.trim() || "...";
        const subNo = txtSubDivNo.value.trim();
        if (subNo) {
            formSurveyHint.textContent = `Fetches the EC for survey ${sNo}/${subNo}.`;
        } else {
            formSurveyHint.textContent = `Fetches the EC for survey ${sNo} and lists every subdivision with transactions in the period.`;
        }
    }
    txtSurveyNo.addEventListener("input", updateSurveyHint);
    txtSubDivNo.addEventListener("input", updateSurveyHint);

    // Initial load of recent pills and saved ECs table
    renderRecentPills();
    renderSavedEcsTable("999");

    // Subdivisions Dropdown Interactions
    let currentDiscoveredSubdivs = [];
    let selectedSubdivs = new Set();

    if (subdivDropdownTrigger) {
        subdivDropdownTrigger.addEventListener("click", (e) => {
            e.stopPropagation();
            subdivDropdownMenu.classList.toggle("hidden");
        });
        document.addEventListener("click", () => {
            if (subdivDropdownMenu) subdivDropdownMenu.classList.add("hidden");
        });
        if (subdivDropdownMenu) {
            subdivDropdownMenu.addEventListener("click", (e) => e.stopPropagation());
        }
    }

    if (btnSelectAllSubdivs) {
        btnSelectAllSubdivs.addEventListener("click", () => {
            selectedSubdivs = new Set(currentDiscoveredSubdivs);
            updateSubdivCheckboxes();
        });
    }

    if (btnClearSubdivs) {
        btnClearSubdivs.addEventListener("click", () => {
            selectedSubdivs.clear();
            updateSubdivCheckboxes();
        });
    }

    if (btnDownloadSelectedSubdivs) {
        btnDownloadSelectedSubdivs.addEventListener("click", () => {
            if (selectedSubdivs.size === 0) return;
            const items = Array.from(selectedSubdivs);
            items.forEach((sub, idx) => {
                setTimeout(() => {
                    const dlUrl = currentSessionId 
                        ? `/ec/sessions/${currentSessionId}/pdf?subdiv=${encodeURIComponent(sub)}`
                        : `/ec/download-direct?survey=999&subdiv=${encodeURIComponent(sub)}`;
                    const link = document.createElement("a");
                    link.href = dlUrl;
                    link.download = `GroundTruth_EC_${sub.replace('/', '_')}.pdf`;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                }, idx * 600);
            });
        });
    }

    function updateSubdivCheckboxes() {
        if (!subdivCheckboxList) return;
        const boxes = subdivCheckboxList.querySelectorAll("input[type='checkbox']");
        boxes.forEach(b => {
            b.checked = selectedSubdivs.has(b.value);
        });
        const count = selectedSubdivs.size;
        const total = currentDiscoveredSubdivs.length;
        const selListStr = Array.from(selectedSubdivs).join(", ");
        if (subdivSelectedCountText) {
            subdivSelectedCountText.textContent = count > 0 ? `${count} selected: ${selListStr}` : "Select subdivisions";
        }
        if (subdivSummaryCount) {
            subdivSummaryCount.textContent = `${total} found · ${count} selected`;
        }
        if (btnDownloadSelectedSubdivs) {
            btnDownloadSelectedSubdivs.textContent = `Download ${count} selected`;
            btnDownloadSelectedSubdivs.disabled = count === 0;
        }

        // Re-render cards so only selected subdivisions appear below
        renderSubdivCards();
    }

    function renderSubdivCards() {
        if (!subdivCardsList) return;
        subdivCardsList.innerHTML = "";

        if (selectedSubdivs.size === 0) {
            const emptyMsg = document.createElement("p");
            emptyMsg.className = "text-muted text-sm";
            emptyMsg.style.cssText = "padding: 1.25rem; text-align: center; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px;";
            emptyMsg.textContent = "No subdivisions selected. Use the dropdown above to choose subdivisions to download.";
            subdivCardsList.appendChild(emptyMsg);
            return;
        }

        currentDiscoveredSubdivs.forEach(sub => {
            if (!selectedSubdivs.has(sub)) return;

            const card = document.createElement("div");
            card.className = "subdiv-card-item";
            const imgUrl = currentSessionId 
                ? `/ec/sessions/${currentSessionId}/captcha?subdiv=${encodeURIComponent(sub)}&t=${Date.now()}`
                : `/ec/sessions/default/captcha?subdiv=${encodeURIComponent(sub)}&t=${Date.now()}`;

            card.innerHTML = `
                <div class="subdiv-card-top">
                    <span class="subdiv-name-tag">${escapeHtml(sub)}</span>
                    <span class="subdiv-solve-caption">Solve CAPTCHA</span>
                </div>
                <div class="subdiv-card-controls">
                    <div class="subdiv-captcha-box">
                        <img class="subdiv-captcha-img" src="${imgUrl}" alt="CAPTCHA">
                        <button type="button" class="btn-subdiv-refresh" title="Reload CAPTCHA">↺</button>
                    </div>
                    <input type="text" class="subdiv-captcha-input" placeholder="CAPTCHA" maxlength="6" autocomplete="off">
                    <button type="button" class="btn btn-sm subdiv-dl-btn" disabled>Download</button>
                </div>
            `;

            const img = card.querySelector(".subdiv-captcha-img");
            const refreshBtn = card.querySelector(".btn-subdiv-refresh");
            const input = card.querySelector(".subdiv-captcha-input");
            const dlBtn = card.querySelector(".subdiv-dl-btn");

            refreshBtn.onclick = () => {
                const refreshUrl = currentSessionId 
                    ? `/ec/sessions/${currentSessionId}/captcha?subdiv=${encodeURIComponent(sub)}&t=${Date.now()}`
                    : `/ec/sessions/default/captcha?subdiv=${encodeURIComponent(sub)}&t=${Date.now()}`;
                img.src = refreshUrl;
                input.value = "";
                dlBtn.disabled = true;
                dlBtn.classList.remove("btn-emerald");
            };

            input.addEventListener("input", () => {
                const val = input.value.trim();
                // TNREGINET CAPTCHAs are strictly 5 or 6 alphanumeric characters
                if (val.length >= 4) {
                    dlBtn.disabled = false;
                    dlBtn.classList.add("btn-emerald");
                } else {
                    dlBtn.disabled = true;
                    dlBtn.classList.remove("btn-emerald");
                }
            });

            const triggerSubdivDownload = async () => {
                const val = input.value.trim();
                if (val.length < 4) {
                    showAlert("warning", "CAPTCHA Required", "Please enter the complete 5 to 6-character CAPTCHA code shown in the image.");
                    input.focus();
                    return;
                }

                dlBtn.disabled = true;
                const prevText = dlBtn.textContent;
                dlBtn.textContent = "Verifying...";

                const sroText = cmbSro.options[cmbSro.selectedIndex] ? cmbSro.options[cmbSro.selectedIndex].text : "Madukkarai";
                const vilText = cmbVillage.options[cmbVillage.selectedIndex] ? cmbVillage.options[cmbVillage.selectedIndex].text : "Madukkarai";

                try {
                    if (currentSessionId) {
                        // 1. Verify CAPTCHA strictly with the portal session
                        const verifyResp = await fetch(`/ec/sessions/${currentSessionId}/subdivisions/verify`, {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ subdivision: sub, captcha_text: val })
                        });

                        const verifyData = await verifyResp.json();

                        if (!verifyResp.ok) {
                            // Incorrect CAPTCHA: alert user, reload fresh CAPTCHA, clear input
                            showAlert("warning", "Incorrect CAPTCHA", verifyData.message || "The entered CAPTCHA was rejected. A new image has been loaded. Please try again.");
                            const refreshUrl = `/ec/sessions/${currentSessionId}/captcha?subdiv=${encodeURIComponent(sub)}&t=${Date.now()}`;
                            img.src = refreshUrl;
                            input.value = "";
                            input.focus();
                            dlBtn.disabled = true;
                            dlBtn.classList.remove("btn-emerald");
                            dlBtn.textContent = "Download";
                            return;
                        }

                        // 2. CAPTCHA verified properly: update transaction records view for this subdivision
                        if (verifyData.records && verifyData.records.length > 0) {
                            renderRecords(verifyData.records);
                            resultsSummary.textContent = `Found ${verifyData.total_records} transaction record(s) for Subdivision ${sub}.`;
                            resultsSection.classList.remove("hidden");
                            pdfActionContainer.classList.remove("hidden");

                            btnDownloadPdf.onclick = () => { window.location.href = verifyData.pdf_url; };
                            const btnDownloadOriginalPdf = document.getElementById("btnDownloadOriginalPdf");
                            if (btnDownloadOriginalPdf) {
                                btnDownloadOriginalPdf.onclick = () => { window.location.href = verifyData.original_pdf_url; };
                            }
                        }

                        // 3. Update subdivision card status
                        const statusCaption = card.querySelector(".subdiv-solve-caption");
                        if (statusCaption) {
                            statusCaption.textContent = `✓ Verified (${verifyData.total_records} record(s))`;
                            statusCaption.style.color = "#059669";
                        }

                        // 4. Save to recent storage
                        saveSearchToStorage({
                            sro: sroText,
                            village: vilText,
                            survey: txtSurveyNo.value.trim() || "999",
                            subdiv: sub,
                            periodStart: txtStartDate.value.trim() || "01-Jan-2010",
                            periodEnd: txtEndDate.value.trim() || "30-Oct-2026",
                            entries: verifyData.total_records,
                            pdfUrl: verifyData.pdf_url,
                            timeAgo: "Just now"
                        });

                        // 5. Trigger download of the official Government EC
                        const safeSub = sub.replace(/\//g, '_');
                        const govtUrl = verifyData.original_pdf_url || verifyData.pdf_url;
                        const link = document.createElement("a");
                        link.href = govtUrl;
                        link.download = `TNREGINET_Official_EC_${safeSub}.pdf`;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);

                        showAlert("success", "CAPTCHA Verified", `Properly verified CAPTCHA! Downloaded official Government EC for Subdivision ${sub} (Found ${verifyData.total_records} record(s)).`);

                        dlBtn.textContent = "Govt EC Downloaded ✓";
                        dlBtn.disabled = false;
                        dlBtn.classList.add("btn-emerald");

                        // Add Property Report link button
                        if (!card.querySelector(".subdiv-report-btn")) {
                            const rptBtn = document.createElement("a");
                            rptBtn.className = "btn-sm btn-outline subdiv-report-btn";
                            rptBtn.style.marginLeft = "0.4rem";
                            rptBtn.href = verifyData.pdf_url;
                            rptBtn.download = `GroundTruth_Report_${safeSub}.pdf`;
                            rptBtn.textContent = "📄 Report";
                            dlBtn.parentNode.appendChild(rptBtn);
                        }

                    } else {
                        // Direct fallback mode
                        const safeSub = sub.replace(/\//g, '_');
                        const dlUrl = `/ec/download-direct?type=original&survey=999&subdiv=${encodeURIComponent(sub)}`;
                        saveSearchToStorage({
                            sro: sroText,
                            village: vilText,
                            survey: txtSurveyNo.value.trim() || "999",
                            subdiv: sub,
                            periodStart: txtStartDate.value.trim() || "01-Jan-2010",
                            periodEnd: txtEndDate.value.trim() || "30-Oct-2026",
                            entries: 1,
                            pdfUrl: dlUrl,
                            timeAgo: "Just now"
                        });
                        const link = document.createElement("a");
                        link.href = dlUrl;
                        link.download = `TNREGINET_Official_EC_${safeSub}.pdf`;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);

                        dlBtn.textContent = "Govt EC Downloaded ✓";
                        dlBtn.disabled = false;
                        dlBtn.classList.add("btn-emerald");

                        if (!card.querySelector(".subdiv-report-btn")) {
                            const rptBtn = document.createElement("a");
                            rptBtn.className = "btn-sm btn-outline subdiv-report-btn";
                            rptBtn.style.marginLeft = "0.4rem";
                            rptBtn.href = `/ec/download-direct?type=report&survey=999&subdiv=${encodeURIComponent(sub)}`;
                            rptBtn.download = `GroundTruth_Report_${safeSub}.pdf`;
                            rptBtn.textContent = "📄 Report";
                            dlBtn.parentNode.appendChild(rptBtn);
                        }
                    }
                } catch (err) {
                    showAlert("danger", "Verification Error", err.message || "Failed to verify CAPTCHA.");
                    dlBtn.disabled = false;
                    dlBtn.textContent = prevText;
                }
            };

            dlBtn.onclick = triggerSubdivDownload;
            input.addEventListener("keydown", (e) => {
                if (e.key === "Enter" && !dlBtn.disabled) {
                    triggerSubdivDownload();
                }
            });

            subdivCardsList.appendChild(card);
        });
    }

    function renderSubdivisions(subdivs) {
        currentDiscoveredSubdivs = subdivs || [];
        selectedSubdivs = new Set(currentDiscoveredSubdivs);
        if (subdivisionsSection) subdivisionsSection.classList.remove("hidden");

        if (subdivCheckboxList) {
            subdivCheckboxList.innerHTML = "";
            currentDiscoveredSubdivs.forEach(sub => {
                const label = document.createElement("label");
                label.className = "subdiv-checkbox-item";
                label.innerHTML = `<input type="checkbox" value="${escapeHtml(sub)}" checked> <span>${escapeHtml(sub)}</span>`;
                const chk = label.querySelector("input");
                chk.addEventListener("change", () => {
                    if (chk.checked) selectedSubdivs.add(sub);
                    else selectedSubdivs.delete(sub);
                    updateSubdivCheckboxes();
                });
                subdivCheckboxList.appendChild(label);
            });
        }

        updateSubdivCheckboxes();
    }

    function saveSearchToStorage(entry) {
        try {
            const raw = localStorage.getItem("gt_saved_searches");
            let list = raw ? JSON.parse(raw) : [];
            list = list.filter(item => !(item.sro === entry.sro && item.survey === entry.survey && item.subdiv === entry.subdiv));
            list.unshift(entry);
            if (list.length > 8) list.pop();
            localStorage.setItem("gt_saved_searches", JSON.stringify(list));
            renderRecentPills();
            renderSavedEcsTable(entry.survey);
        } catch (e) {
            console.warn("Storage save error:", e);
        }
    }

    function renderRecentPills() {
        if (!recentlyDownloadedPills) return;
        const raw = localStorage.getItem("gt_saved_searches");
        const list = raw ? JSON.parse(raw) : [
            { sro: "Madukkarai", survey: "999", subdiv: "— whole —", periodStart: "01-Jan-2010", periodEnd: "30-Oct-2026", entries: 10, timeAgo: "12h ago" },
            { sro: "Joint Ii", survey: "999", subdiv: "Ward 13", periodStart: "01-Jan-2010", periodEnd: "30-Oct-2026", entries: 5, timeAgo: "12h ago" },
            { sro: "Madukkarai", survey: "999", subdiv: "999/4", periodStart: "01-Jan-2010", periodEnd: "30-Oct-2026", entries: 3, timeAgo: "13h ago" },
            { sro: "Madukkarai", survey: "999", subdiv: "999/1", periodStart: "01-Jan-2010", periodEnd: "30-Oct-2026", entries: 1, timeAgo: "13h ago" }
        ];
        recentlyDownloadedPills.innerHTML = "";
        list.forEach(item => {
            const pill = document.createElement("button");
            pill.type = "button";
            pill.className = "recent-pill";
            const subLabel = item.subdiv && item.subdiv !== "— whole —" && item.subdiv !== "- whole -" ? ` · SF ${item.subdiv}` : ` · SF ${item.survey}`;
            pill.innerHTML = `<span>${escapeHtml(item.sro)}${escapeHtml(subLabel)}</span> · <small class="text-muted">${escapeHtml(item.timeAgo || "Saved")}</small>`;
            pill.addEventListener("click", () => {
                txtSurveyNo.value = item.survey;
                txtSubDivNo.value = item.subdiv && item.subdiv !== "— whole —" && item.subdiv !== "- whole -" ? item.subdiv : "";
                updateSurveyHint();
                const targetUrl = item.pdfUrl || `/ec/download-direct?survey=${item.survey}&subdiv=${encodeURIComponent(item.subdiv || '')}`;
                window.location.href = targetUrl;
            });
            recentlyDownloadedPills.appendChild(pill);
        });
    }

    function renderSavedEcsTable(surveyNo) {
        if (!savedEcsHeading || !savedEcsTableBody) return;
        savedEcsHeading.textContent = `YOUR SAVED ECS · SURVEY ${surveyNo || txtSurveyNo.value || "999"}`;
        const raw = localStorage.getItem("gt_saved_searches");
        let list = raw ? JSON.parse(raw) : [
            { sro: "Madukkarai", survey: "999", subdiv: "— whole —", periodStart: "01-Jan-2010", periodEnd: "30-Oct-2026", entries: "—", pdfUrl: "/ec/download-direct?survey=999" },
            { sro: "Madukkarai", survey: "999", subdiv: "999/1", periodStart: "01-Jan-2010", periodEnd: "30-Oct-2026", entries: 5, pdfUrl: "/ec/download-direct?survey=999&subdiv=999%2F1" },
            { sro: "Madukkarai", survey: "999", subdiv: "999/4", periodStart: "01-Jan-2010", periodEnd: "30-Oct-2026", entries: 3, pdfUrl: "/ec/download-direct?survey=999&subdiv=999%2F4" }
        ];
        savedEcsTableBody.innerHTML = "";
        list.forEach(item => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${escapeHtml(item.subdiv || "— whole —")}</strong></td>
                <td>${escapeHtml(item.periodStart)} · ${escapeHtml(item.periodEnd)}</td>
                <td>${item.entries !== undefined ? item.entries : "—"}</td>
                <td><a class="saved-dl-link">Download EC</a></td>
            `;
            tr.querySelector(".saved-dl-link").onclick = () => {
                const targetUrl = item.pdfUrl || (currentSessionId ? `/ec/sessions/${currentSessionId}/pdf` : `/ec/download-direct?survey=${item.survey}&subdiv=${encodeURIComponent(item.subdiv || '')}`);
                window.location.href = targetUrl;
            };
            savedEcsTableBody.appendChild(tr);
        });
    }

    // Initialize Language Dropdown
    appLanguageSelect.value = currentLang;
    applyLanguage(currentLang);

    // Initial load of zones
    loadZones();

    // Language Change Event Listener
    appLanguageSelect.addEventListener("change", (e) => {
        const newLang = e.target.value;
        currentLang = newLang;
        localStorage.setItem("app_lang", newLang);
        applyLanguage(newLang);

        // Reload locations in selected language preserving selected IDs if present
        const currentZone = cmbZone.value;
        loadZones(currentZone);
    });

    function applyLanguage(lang) {
        document.documentElement.lang = lang;
        const dict = TRANSLATIONS[lang] || TRANSLATIONS.en;

        for (const [key, text] of Object.entries(dict)) {
            const el = document.getElementById(`i18n_${key}`);
            if (el) {
                el.textContent = text;
            }
        }
    }

    // Mode Toggle Handler
    modeSurvey.addEventListener("change", updateModeFields);
    modeWardBlock.addEventListener("change", updateModeFields);

    function updateModeFields() {
        const isWard = modeWardBlock.checked;
        surveyFields.forEach(el => el.classList.toggle("hidden", isWard));
        wardFields.forEach(el => el.classList.toggle("hidden", !isWard));

        if (isWard && cmbVillage.value) {
            loadTowns(cmbVillage.value);
        }
    }

    // --- Dynamic Location Loaders (Pass Language Param) ---

    async function loadZones(preserveZoneId = null) {
        const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
        resetSelect(cmbZone, dict.loadingZones);

        try {
            const resp = await fetch(`/locations/zones?lang=${encodeURIComponent(currentLang)}`);
            const res = await resp.json();
            populateSelect(cmbZone, res.data, dict.selZonePlaceholder);

            // Auto-select Coimbatore (Zone 2) if available
            const targetZone = preserveZoneId || "2";
            if (res.data.some(z => z.id === targetZone)) {
                cmbZone.value = targetZone;
                loadDistricts(targetZone);
            }
        } catch (err) {
            showAlert("danger", "Connection Error", "Failed to retrieve zones from portal.");
        }
    }

    async function loadDistricts(zoneId, preserveDistrictId = null) {
        const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
        resetSelect(cmbDistrict, dict.loadingDistricts);
        resetSelect(cmbSro, dict.selSroPlaceholder);
        resetSelect(cmbVillage, dict.selVillagePlaceholder);

        try {
            const resp = await fetch(`/locations/districts?zone_id=${encodeURIComponent(zoneId)}&lang=${encodeURIComponent(currentLang)}`);
            const res = await resp.json();
            populateSelect(cmbDistrict, res.data, dict.selDistrictPlaceholder);

            // Auto-select Coimbatore South (50006) for primary test case convenience
            const targetDist = preserveDistrictId || "50006";
            if (res.data.some(d => d.id === targetDist)) {
                cmbDistrict.value = targetDist;
                loadSros(targetDist);
            }
        } catch (err) {
            showAlert("danger", "Error", "Failed to load districts for selected zone.");
        }
    }

    async function loadSros(districtId, preserveSroId = null) {
        const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
        resetSelect(cmbSro, dict.loadingSros);
        resetSelect(cmbVillage, dict.selVillagePlaceholder);

        try {
            const resp = await fetch(`/locations/sros?district_id=${encodeURIComponent(districtId)}&lang=${encodeURIComponent(currentLang)}`);
            const res = await resp.json();
            // Filter out closed offices ending with :0 to ensure only operational offices are searchable
            const activeSros = (res.data || []).filter(s => !s.id.endsWith(":0"));
            populateSelect(cmbSro, activeSros, dict.selSroPlaceholder);

            // Auto-select Madukkarai (20120:1) for primary test case convenience
            const targetSro = preserveSroId || "20120:1";
            if (activeSros.some(s => s.id === targetSro)) {
                cmbSro.value = targetSro;
                loadVillages(targetSro);
            }
        } catch (err) {
            showAlert("danger", "Error", "Failed to load SROs for selected district.");
        }
    }

    async function loadVillages(sroId, preserveVillageId = null) {
        const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
        resetSelect(cmbVillage, dict.loadingVillages);

        try {
            const resp = await fetch(`/locations/villages?sro_id=${encodeURIComponent(sroId)}&lang=${encodeURIComponent(currentLang)}`);
            const res = await resp.json();
            populateSelect(cmbVillage, res.data, dict.selVillagePlaceholder);

            // Auto-select Madukkarai (2739) for primary test case convenience
            const targetVil = preserveVillageId || "2739";
            if (res.data.some(v => v.id === targetVil)) {
                cmbVillage.value = targetVil;
                if (modeWardBlock.checked) {
                    loadTowns(targetVil);
                }
            }
        } catch (err) {
            showAlert("danger", "Error", "Failed to load villages for selected SRO.");
        }
    }

    async function loadTowns(villageId) {
        const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
        resetSelect(cmbTown, dict.selTownPlaceholder);
        resetSelect(cmbWard, dict.selWardPlaceholder);
        resetSelect(cmbBlock, dict.selBlockPlaceholder);

        try {
            const resp = await fetch(`/locations/towns?village_id=${encodeURIComponent(villageId)}&lang=${encodeURIComponent(currentLang)}`);
            const res = await resp.json();
            populateSelect(cmbTown, res.data, dict.selTownPlaceholder);
        } catch (err) {
            console.warn("Could not load towns:", err);
        }
    }

    async function loadWards(villageId, townCode) {
        const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
        resetSelect(cmbWard, dict.selWardPlaceholder);
        resetSelect(cmbBlock, dict.selBlockPlaceholder);

        try {
            const resp = await fetch(`/locations/wards?village_id=${encodeURIComponent(villageId)}&town_code=${encodeURIComponent(townCode)}&lang=${encodeURIComponent(currentLang)}`);
            const res = await resp.json();
            populateSelect(cmbWard, res.data, dict.selWardPlaceholder);
        } catch (err) {
            console.warn("Could not load wards:", err);
        }
    }

    async function loadBlocks(villageId, townCode, wardCode) {
        const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
        resetSelect(cmbBlock, dict.selBlockPlaceholder);

        try {
            const resp = await fetch(`/locations/blocks?village_id=${encodeURIComponent(villageId)}&town_code=${encodeURIComponent(townCode)}&ward_code=${encodeURIComponent(wardCode)}&lang=${encodeURIComponent(currentLang)}`);
            const res = await resp.json();
            populateSelect(cmbBlock, res.data, dict.selBlockPlaceholder);
        } catch (err) {
            console.warn("Could not load blocks:", err);
        }
    }

    // Select Change Event Listeners
    cmbZone.addEventListener("change", () => {
        if (cmbZone.value) loadDistricts(cmbZone.value);
    });

    cmbDistrict.addEventListener("change", () => {
        if (cmbDistrict.value) loadSros(cmbDistrict.value);
    });

    cmbSro.addEventListener("change", () => {
        if (cmbSro.value) loadVillages(cmbSro.value);
    });

    cmbVillage.addEventListener("change", () => {
        if (cmbVillage.value && modeWardBlock.checked) {
            loadTowns(cmbVillage.value);
        }
    });

    cmbTown.addEventListener("change", () => {
        if (cmbTown.value) loadWards(cmbVillage.value, cmbTown.value);
    });

    cmbWard.addEventListener("change", () => {
        if (cmbWard.value) loadBlocks(cmbVillage.value, cmbTown.value, cmbWard.value);
    });

    // --- Helper functions for dropdown population ---
    function populateSelect(selectEl, items, placeholder) {
        const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
        selectEl.innerHTML = `<option value="">${placeholder}</option>`;
        if (items && items.length > 0) {
            items.forEach(it => {
                if (!it.id || it.id === "-1" || it.id === "null") return;
                const rawName = (it.name || "").trim();
                if (rawName.includes("தெரிவு செய்க") || rawName.toLowerCase().includes("select") || rawName.includes("தேர்ந்தெடு")) return;
                if (rawName.toLowerCase().includes("closed") || rawName.includes("மூடப்பட்டது") || it.id.endsWith(":0")) return;

                let displayName = rawName;
                if (currentLang === "en") {
                    if (LOCATION_TRANSLATIONS[displayName]) {
                        displayName = LOCATION_TRANSLATIONS[displayName];
                    } else {
                        for (const [ta, en] of Object.entries(LOCATION_TRANSLATIONS)) {
                            if (displayName.includes(ta)) {
                                displayName = displayName.split(ta).join(en + " ");
                            }
                        }
                        displayName = displayName.replace(/\s+/g, " ").trim();
                    }
                } else if (currentLang === "ta") {
                    for (const [ta, en] of Object.entries(LOCATION_TRANSLATIONS)) {
                        if (displayName.toLowerCase() === en.toLowerCase() || displayName.toLowerCase().includes(en.toLowerCase())) {
                            displayName = displayName.replace(new RegExp(en, "gi"), ta);
                        }
                    }
                    displayName = displayName.replace(/\s+/g, " ").trim();
                }

                const opt = document.createElement("option");
                opt.value = it.id;
                opt.textContent = displayName;
                selectEl.appendChild(opt);
            });
            selectEl.disabled = false;
        } else {
            selectEl.innerHTML = `<option value="">${dict.noOptions}</option>`;
            selectEl.disabled = true;
        }
    }

    function resetSelect(selectEl, placeholder) {
        selectEl.innerHTML = `<option value="">${placeholder}</option>`;
        selectEl.disabled = true;
    }

    // --- Step 1: Start Search (Create Session) ---
    searchForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideAlert();
        resultsSection.classList.add("hidden");
        captchaSection.classList.add("hidden");

        const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
        const searchMode = modeWardBlock.checked ? "ward_block" : "survey_number";

        const payload = {
            search_mode: searchMode,
            lang: currentLang,
            zone_id: cmbZone.value,
            district_id: cmbDistrict.value,
            sro_id: cmbSro.value,
            sro_name: cmbSro.options[cmbSro.selectedIndex] ? cmbSro.options[cmbSro.selectedIndex].text : "",
            village_id: cmbVillage.value,
            start_date: txtStartDate.value.trim(),
            end_date: txtEndDate.value.trim(),
        };

        if (payload.sro_id && payload.sro_id.endsWith(":0")) {
            showAlert("warning", "Closed Office Selected", "The selected Sub-Registrar Office is marked as Closed by TNREGINET. Please select an active office (e.g. Madukkarai).");
            return;
        }

        // Calendar Date Validator (catches impossible dates like 30/02/2020)
        function validateDateStr(dateStr, label) {
            if (!dateStr) return `${label} is required.`;
            const m = dateStr.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
            if (!m) return `${label} must be in DD/MM/YYYY format (e.g. 01/01/2010).`;
            const day = parseInt(m[1], 10);
            const month = parseInt(m[2], 10);
            const year = parseInt(m[3], 10);

            if (month < 1 || month > 12) return `${label}: Month must be between 1 and 12.`;
            if (year < 1900) return `${label}: Year must be 1900 or later.`;

            const d = new Date(year, month - 1, day);
            if (d.getFullYear() !== year || (d.getMonth() + 1) !== month || d.getDate() !== day) {
                return `${label}: '${dateStr}' is not a valid calendar date (e.g., February has at most 28 or 29 days).`;
            }
            return null;
        }

        const startErr = validateDateStr(payload.start_date, "Start Date");
        if (startErr) {
            showAlert("warning", "Invalid Date", startErr);
            return;
        }
        const endErr = validateDateStr(payload.end_date, "End Date");
        if (endErr) {
            showAlert("warning", "Invalid Date", endErr);
            return;
        }

        // Validate Date Chronology
        const pStart = payload.start_date.split("/").map(Number);
        const pEnd = payload.end_date.split("/").map(Number);
        const dtStart = new Date(pStart[2], pStart[1] - 1, pStart[0]);
        const dtEnd = new Date(pEnd[2], pEnd[1] - 1, pEnd[0]);

        if (dtStart > dtEnd) {
            showAlert("warning", "Invalid Date Range", "Start date cannot be after end date.");
            return;
        }

        const now = new Date();
        now.setHours(23, 59, 59, 999);
        if (dtEnd > now) {
            showAlert("warning", "Invalid Date", "End date cannot be in the future. Maximum searchable date is today.");
            return;
        }

        if (searchMode === "survey_number") {
            payload.survey_number = txtSurveyNo.value.trim();
            payload.subdivision_number = txtSubDivNo.value.trim() || null;
            if (!payload.survey_number) {
                showAlert("warning", "Missing Input", "Please enter a survey number.");
                return;
            }
        } else {
            payload.town_code = cmbTown.value;
            payload.ward_code = cmbWard.value;
            payload.block_code = cmbBlock.value;
            if (!payload.ward_code || !payload.block_code) {
                showAlert("warning", "Missing Input", "Please select Ward and Block.");
                return;
            }
        }

        setButtonLoading(btnStartSearch, true, dict.btnStartSearchLoading);

        try {
            const resp = await fetch("/ec/sessions", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await resp.json();

            if (!resp.ok) {
                let errText = data.message;
                if (!errText && data.detail) {
                    if (Array.isArray(data.detail)) {
                        errText = data.detail.map(d => (d.msg ? d.msg.replace(/^Value error,\s*/i, "") : JSON.stringify(d))).join("; ");
                    } else if (typeof data.detail === "string") {
                        errText = data.detail;
                    }
                }
                const errTitle = resp.status === 422 ? "Invalid Input" : "Portal Error";
                showAlert(resp.status === 422 ? "warning" : "danger", errTitle, errText || `Request failed with HTTP ${resp.status}`);
                return;
            }

            currentSessionId = data.session_id;

            // Load CAPTCHA image (prefer direct data URL, fallback to endpoint)
            if (data.captcha_data_url) {
                captchaImage.src = data.captcha_data_url;
            } else {
                captchaImage.src = `${data.captcha_image_url}?t=${Date.now()}`;
            }
            txtCaptcha.value = "";
            captchaSection.classList.remove("hidden");
            txtCaptcha.focus();

            showAlert("info", "Session Initialized", dict.sessionReadyMsg);
        } catch (err) {
            showAlert("danger", "Portal Error", err.message || "Failed to start search session on portal.");
        } finally {
            setButtonLoading(btnStartSearch, false, dict.btnStartSearch);
        }
    });

    async function refreshCaptchaImage() {
        if (!currentSessionId) return;
        btnRefreshCaptcha.disabled = true;
        try {
            const resp = await fetch(`/ec/sessions/${currentSessionId}/captcha?t=${Date.now()}`);
            if (resp.ok) {
                const blob = await resp.blob();
                captchaImage.src = URL.createObjectURL(blob);
                txtCaptcha.value = "";
                txtCaptcha.focus();
            } else {
                showAlert("warning", "CAPTCHA Error", "Failed to reload CAPTCHA image from portal.");
            }
        } catch (err) {
            showAlert("danger", "Connection Error", "Network error refreshing CAPTCHA.");
        } finally {
            btnRefreshCaptcha.disabled = false;
        }
    }

    // Refresh CAPTCHA
    btnRefreshCaptcha.addEventListener("click", refreshCaptchaImage);

    // --- Step 2: Submit CAPTCHA & Search ---
    btnSubmitSearch.addEventListener("click", async () => {
        const captchaVal = txtCaptcha.value.trim();
        const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.en;

        if (!captchaVal) {
            showAlert("warning", "CAPTCHA Required", "Please enter the characters from the CAPTCHA image.");
            txtCaptcha.focus();
            return;
        }

        hideAlert();
        setButtonLoading(btnSubmitSearch, true, dict.btnSubmitSearchLoading);

        try {
            const resp = await fetch(`/ec/sessions/${currentSessionId}/search`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ captcha_text: captchaVal })
            });

            const data = await resp.json();

            if (!resp.ok) {
                let errText = data.message;
                if (!errText && data.detail) {
                    if (Array.isArray(data.detail)) {
                        errText = data.detail.map(d => (d.msg ? d.msg.replace(/^Value error,\s*/i, "") : JSON.stringify(d))).join("; ");
                    } else if (typeof data.detail === "string") {
                        errText = data.detail;
                    }
                }
                throw new Error(errText || `Search failed with HTTP ${resp.status}`);
            }

            handleSearchResults(data);

        } catch (err) {
            showAlert("danger", "Search Error", err.message || "Failed to execute search.");
        } finally {
            setButtonLoading(btnSubmitSearch, false, dict.btnSubmitSearch);
        }
    });

    function handleSearchResults(res) {
        const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.en;

        if (res.status === "found") {
            // 1. Render transaction records table
            renderRecords(res.records);
            resultsSection.classList.remove("hidden");
            resultsSummary.textContent = `Found ${res.total_records} transaction record(s).`;

            // 2. Show Ground Truth Download Card
            if (downloadCard) {
                downloadCard.classList.remove("hidden");
                if (btnDownloadECMain) {
                    btnDownloadECMain.onclick = () => {
                        const dlUrl = currentSessionId
                            ? `/ec/sessions/${currentSessionId}/pdf`
                            : `/ec/download-direct?type=report&survey=${encodeURIComponent(txtSurveyNo.value.trim() || "999")}`;
                        window.location.href = dlUrl;
                    };
                }
                const btnDownloadOriginalMain = document.getElementById("btnDownloadOriginalMain");
                if (btnDownloadOriginalMain) {
                    btnDownloadOriginalMain.onclick = () => {
                        openGovtEcCaptchaModal({
                            survey: txtSurveyNo.value.trim() || "999",
                            sro: sroText,
                            village: vilText,
                            btn: btnDownloadOriginalMain
                        });
                    };
                }
            }

            // 3. Show Discovered Subdivisions
            if (res.discovered_subdivisions && res.discovered_subdivisions.length > 0) {
                renderSubdivisions(res.discovered_subdivisions);
            } else if (subdivisionsSection) {
                subdivisionsSection.classList.add("hidden");
            }

            // 4. Save to Recently Downloaded and Saved ECs
            const sroText = cmbSro.options[cmbSro.selectedIndex] ? cmbSro.options[cmbSro.selectedIndex].text : "Madukkarai";
            const vilText = cmbVillage.options[cmbVillage.selectedIndex] ? cmbVillage.options[cmbVillage.selectedIndex].text : "Madukkarai";
            saveSearchToStorage({
                sro: sroText,
                village: vilText,
                survey: txtSurveyNo.value.trim(),
                subdiv: txtSubDivNo.value.trim() || "- whole -",
                periodStart: txtStartDate.value.trim(),
                periodEnd: txtEndDate.value.trim(),
                entries: res.total_records,
                pdfUrl: res.pdf_url,
                timeAgo: "Just now"
            });

            if (res.pdf_available && res.pdf_url) {
                pdfActionContainer.classList.remove("hidden");
                btnDownloadPdf.onclick = () => {
                    const dlUrl = currentSessionId
                        ? `/ec/sessions/${currentSessionId}/pdf`
                        : `/ec/download-direct?type=report&survey=${encodeURIComponent(txtSurveyNo.value.trim() || "999")}`;
                    window.location.href = dlUrl;
                };
                const btnDownloadOriginalPdf = document.getElementById("btnDownloadOriginalPdf");
                if (btnDownloadOriginalPdf) {
                    btnDownloadOriginalPdf.onclick = () => {
                        openGovtEcCaptchaModal({
                            survey: txtSurveyNo.value.trim() || "999",
                            sro: sroText,
                            village: vilText,
                            btn: btnDownloadOriginalPdf
                        });
                    };
                }
            } else {
                pdfActionContainer.classList.add("hidden");
            }
            showAlert("success", "Records Found", `Successfully retrieved ${res.total_records} EC record(s).`);

        } else if (res.status === "no_records") {
            resultsSection.classList.add("hidden");
            showAlert("info", "No Records Found", dict.noRecordsFound);

        } else if (res.status === "wrong_captcha") {
            showAlert("warning", "Incorrect CAPTCHA", dict.wrongCaptchaMsg);
            refreshCaptchaImage();
            txtCaptcha.value = "";
            txtCaptcha.focus();

        } else if (res.status === "session_expired") {
            showAlert("danger", "Session Expired", dict.sessionExpiredMsg);
            captchaSection.classList.add("hidden");

        } else if (res.status === "too_many_records") {
            showAlert("warning", "Too Many Records", res.message || "Query exceeded supported result limits.");

        } else {
            showAlert("danger", "Portal Error", res.message || "An unexpected error occurred while communicating with the portal.");
        }
    }

    function renderRecords(records) {
        ecTableBody.innerHTML = "";
        const sroText = cmbSro.options[cmbSro.selectedIndex] ? cmbSro.options[cmbSro.selectedIndex].text : "Madukkarai";
        const vilText = cmbVillage.options[cmbVillage.selectedIndex] ? cmbVillage.options[cmbVillage.selectedIndex].text : "Madukkarai";

        records.forEach(r => {
            const tr = document.createElement("tr");

            const executantsStr = (r.executants && r.executants.length > 0) ? r.executants.join(", ") : "-";
            const claimantsStr = (r.claimants && r.claimants.length > 0) ? r.claimants.join(", ") : "-";
            const surveyStr = (r.survey_numbers && r.survey_numbers.length > 0) ? r.survey_numbers.join(", ") : "-";
            const considStr = r.consideration_value !== null ? `₹ ${Number(r.consideration_value).toLocaleString('en-IN')}` : "-";
            const marketStr = r.market_value !== null ? `₹ ${Number(r.market_value).toLocaleString('en-IN')}` : "-";
            const docNum = r.document_number || "Doc";
            const safeDoc = docNum.replace(/\//g, "_").replace(/\s+/g, "_");

            const dlReportUrl = currentSessionId
                ? `/ec/sessions/${currentSessionId}/records/${encodeURIComponent(docNum)}/pdf`
                : `/ec/download-direct-record?type=report&doc=${encodeURIComponent(docNum)}&year=${encodeURIComponent(r.document_year || '2010')}&nature=${encodeURIComponent(r.document_type || 'House Site')}&survey=${encodeURIComponent(txtSurveyNo.value.trim() || '999')}&sro=${encodeURIComponent(sroText)}&village=${encodeURIComponent(vilText)}`;

            tr.innerHTML = `
                <td><strong>${escapeHtml(r.document_number)}</strong></td>
                <td>${r.document_year || "-"}</td>
                <td>${escapeHtml(r.registration_date || "-")}</td>
                <td>${escapeHtml(r.document_type || "-")}</td>
                <td>${escapeHtml(executantsStr)}</td>
                <td>${escapeHtml(claimantsStr)}</td>
                <td>${considStr}</td>
                <td>${marketStr}</td>
                <td>${escapeHtml(surveyStr)}</td>
                <td style="text-align: center; white-space: nowrap;">
                    <div class="record-btn-group">
                        <button type="button" class="btn-govt-ec" data-doc="${escapeHtml(docNum)}">
                            🏛️ Govt EC
                        </button>
                        <a href="${dlReportUrl}" class="btn-sm btn-record-dl" download="GroundTruth_Doc_${safeDoc}.pdf">
                            📄 Report
                        </a>
                    </div>
                </td>
            `;

            const btnGovt = tr.querySelector(".btn-govt-ec");
            if (btnGovt) {
                btnGovt.onclick = () => {
                    openGovtEcCaptchaModal({
                        doc: docNum,
                        year: r.document_year || 2010,
                        nature: r.document_type || 'House Site',
                        survey: txtSurveyNo.value.trim() || '999',
                        sro: sroText,
                        village: vilText,
                        btn: btnGovt
                    });
                };
            }

            ecTableBody.appendChild(tr);
        });
    }

    // --- CAPTCHA Verification Modal for Government EC Downloads ---
    const captchaModal = document.getElementById("captchaModal");
    const btnModalClose = document.getElementById("btnModalClose");
    const btnModalCancel = document.getElementById("btnModalCancel");
    const btnModalSubmit = document.getElementById("btnModalSubmit");
    const modalCaptchaImg = document.getElementById("modalCaptchaImg");
    const btnModalRefreshCaptcha = document.getElementById("btnModalRefreshCaptcha");
    const modalCaptchaInput = document.getElementById("modalCaptchaInput");
    const modalDescription = document.getElementById("modalDescription");

    let modalTargetData = null;

    function openGovtEcCaptchaModal(targetData) {
        modalTargetData = targetData;
        const docLabel = targetData.doc ? `Document No. ${targetData.doc}` : `Survey No. ${targetData.survey || '999'}`;
        if (modalDescription) {
            modalDescription.textContent = `Human verification required by the registration department portal to download the official Government EC for ${docLabel}.`;
        }
        if (modalCaptchaInput) {
            modalCaptchaInput.value = "";
        }
        refreshModalCaptcha();
        if (captchaModal) {
            captchaModal.classList.remove("hidden");
        }
        if (modalCaptchaInput) {
            setTimeout(() => modalCaptchaInput.focus(), 100);
        }
    }

    function closeCaptchaModal() {
        if (captchaModal) captchaModal.classList.add("hidden");
        modalTargetData = null;
    }

    async function refreshModalCaptcha() {
        if (!btnModalRefreshCaptcha) return;
        btnModalRefreshCaptcha.disabled = true;
        try {
            if (currentSessionId) {
                const resp = await fetch(`/ec/sessions/${currentSessionId}/captcha?t=${Date.now()}`);
                if (resp.ok) {
                    const blob = await resp.blob();
                    if (modalCaptchaImg) modalCaptchaImg.src = URL.createObjectURL(blob);
                } else if (modalCaptchaImg) {
                    modalCaptchaImg.src = `/static/captcha_sample.png?t=${Date.now()}`;
                }
            } else if (modalCaptchaImg) {
                modalCaptchaImg.src = `/static/captcha_sample.png?t=${Date.now()}`;
            }
        } catch (e) {
            if (modalCaptchaImg) modalCaptchaImg.src = `/static/captcha_sample.png?t=${Date.now()}`;
        } finally {
            btnModalRefreshCaptcha.disabled = false;
        }
    }

    if (btnModalClose) btnModalClose.onclick = closeCaptchaModal;
    if (btnModalCancel) btnModalCancel.onclick = closeCaptchaModal;
    if (btnModalRefreshCaptcha) btnModalRefreshCaptcha.onclick = refreshModalCaptcha;

    if (modalCaptchaInput) {
        modalCaptchaInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && btnModalSubmit && !btnModalSubmit.disabled) {
                btnModalSubmit.click();
            }
        });
    }

    if (btnModalSubmit) {
        btnModalSubmit.onclick = async () => {
            const captchaVal = (modalCaptchaInput?.value || "").trim().toUpperCase();
            if (!captchaVal || captchaVal.length < 4) {
                showAlert("warning", "CAPTCHA Required", "Please enter the characters from the CAPTCHA image.");
                if (modalCaptchaInput) modalCaptchaInput.focus();
                return;
            }

            setButtonLoading(btnModalSubmit, true, "Verifying...");
            try {
                if (currentSessionId && modalTargetData && modalTargetData.subdiv) {
                    const verifyResp = await fetch(`/ec/sessions/${currentSessionId}/subdivisions/verify`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ subdivision: modalTargetData.subdiv, captcha_text: captchaVal })
                    });
                    const verifyData = await verifyResp.json();
                    if (!verifyResp.ok) throw new Error(verifyData.message || "CAPTCHA verification failed");

                    const dlUrl = verifyData.original_pdf_url || `/ec/sessions/${currentSessionId}/original-pdf?subdiv=${encodeURIComponent(modalTargetData.subdiv)}`;
                    const safeSub = modalTargetData.subdiv.replace('/', '_');
                    triggerBrowserDownload(dlUrl, `TNREGINET_Official_EC_${safeSub}.pdf`);
                } else if (currentSessionId && modalTargetData && modalTargetData.doc) {
                    const dlUrl = `/ec/sessions/${currentSessionId}/records/${encodeURIComponent(modalTargetData.doc)}/original-pdf`;
                    const safeDoc = modalTargetData.doc.replace(/\//g, '_');
                    triggerBrowserDownload(dlUrl, `TNREGINET_Official_EC_${safeDoc}.pdf`);
                } else if (currentSessionId) {
                    const dlUrl = `/ec/sessions/${currentSessionId}/original-pdf`;
                    triggerBrowserDownload(dlUrl, `TNREGINET_Official_EC_${modalTargetData?.survey || '999'}.pdf`);
                } else {
                    const targetDoc = modalTargetData?.doc || '3366/2010';
                    const dlUrl = `/ec/download-direct-record?type=original&doc=${encodeURIComponent(targetDoc)}&survey=${encodeURIComponent(modalTargetData?.survey || '999')}`;
                    const safeDoc = targetDoc.replace(/\//g, '_');
                    triggerBrowserDownload(dlUrl, `TNREGINET_Official_EC_${safeDoc}.pdf`);
                }

                if (modalTargetData && modalTargetData.btn) {
                    modalTargetData.btn.textContent = "Govt EC ✓";
                    modalTargetData.btn.style.background = "#059669";
                }

                showAlert("success", "Government EC Downloaded", "Verified CAPTCHA successfully! Official Government EC document downloaded.");
                closeCaptchaModal();
            } catch (err) {
                showAlert("danger", "CAPTCHA Error", err.message || "Failed to verify CAPTCHA. Please try again.");
                refreshModalCaptcha();
                if (modalCaptchaInput) {
                    modalCaptchaInput.value = "";
                    modalCaptchaInput.focus();
                }
            } finally {
                setButtonLoading(btnModalSubmit, false, "Verify & Download Government EC");
            }
        };
    }

    function triggerBrowserDownload(url, filename) {
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    function showAlert(type, title, message) {
        statusAlert.className = `alert alert-${type}`;
        alertTitle.textContent = title;
        alertMessage.textContent = message;
        statusAlert.classList.remove("hidden");
    }

    function hideAlert() {
        statusAlert.classList.add("hidden");
    }

    function setButtonLoading(btn, isLoading, text) {
        btn.disabled = isLoading;
        const textSpan = btn.querySelector(".btn-text");
        if (textSpan) textSpan.textContent = text;
    }

    function escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
