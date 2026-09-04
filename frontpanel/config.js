// ========== Front Panel Remote Configuration ==========
// Each entry = one Extron. Add, remove, and rename as needed.

const DEVICES = [
	// Matrix 1
    {name: 'Crosspoint Ultra 128HVA', 	// Enter matrix name
		ip: '192.168.1.252',			// Enter matrix IP address
		numInputs: 		12,				// Enter total inputs of matrix
		numOutputs: 	08,				// Enter total outputs of matrix
		imageDir: '/images/',			// Directory of button images relative to location of panel webpage
		inputImages: {					// File names for input buttom images. Add lines in same format for each input.
			1: 'psx-crt-c.png',
			2: 'ps2-crt-c.png',
			3: 'ps3-crt-c.png',
			4: 'nes-crt-c.png',
        },
        outputImages: {					// File names for output buttom images. Add lines in same format for each output.
			1: '',						// Empty or missing buttons will show as just the number.
			2: '',
			3: '',
        },
    },
	
	// Matrix 2 (Remove if using only one)
    {name: 'DXP HDMI 84',
		ip: '192.168.1.249',
        numInputs: 		08,
        numOutputs: 	04,
        imageDir: '/images/',
        inputImages: {
			1: 'ps3-crt-c.png',
			2: 'ps4-crt-c.png',
			3: 'pstv-crt-c.png',
			4: 'xbox360-crt-c.png',
        },
        outputImages: {
			1: '',
			2: '',
			3: '',
        },
    },
	

	
	
    // Add more matrix devices above this line
];
    