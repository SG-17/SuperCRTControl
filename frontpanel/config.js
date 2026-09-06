// ========== Front Panel Remote Configuration ==========
// Each entry = one Extron. Add, remove, and rename as needed.

const DEVICES = [
	// Matrix 1
    {	name: 'Crosspoint Ultra 128HVA', 	// Enter matrix name
		ip: '192.168.1.252',				// Enter matrix IP address
		numInputs: 		12,					// Enter total inputs of matrix
		numOutputs: 	08,					// Enter total outputs of matrix
		imageDir: 'images/',				// Directory of button images relative to location of panel webpage
		inputImages: {						// File names for input buttom images. Add lines in same format for each input.
			1: 'psx-crt-c.png',
			2: 'ps2-crt-c.png',
			3: 'ps3-crt-c.png',
			4: 'nes-crt-c.png',
			5: 'snes-crt-c.png',
			6: 'n64-crt-c.png',
			7: 'gamecube-crt-c.png',
			8: 'wii-crt-c.png',
			9: 'genesis-crt-c.png',
			10: 'vhs-crt-c.png',
			11: 'tvgames-crt-c.png',
			12: '480P-480I.png',
        },
        outputImages: {						// File names for output buttom images. Add lines in same format for each output.
			1: '5XPRO.png',					// Empty or missing buttons will show as just the number.
			2: 'CRT-YPBPR.png',
			3: 'CRT-YC.png',
			4: 'CRT-CVBS.png',
			5: '4kpro-crt-c.png',
			6: '',
			7: '',
			8: '',
        },
    },
	
	// Matrix 2
    {	name: 'DXP HDMI 84',
		ip: '192.168.1.249',
        numInputs: 		08,
        numOutputs: 	04,
        imageDir: 'images/',
        inputImages: {
			1: 'ps3-crt-c.png',
			2: 'ps4-crt-c.png',
			3: 'pstv-crt-c.png',
			4: 'xbox360-crt-c.png',
			5: 'gamecube-crt-c.png',
			6: 'nsw-crt-c.png',
			7: 'DXPHD4KPLUS.png',
			8: '',
        },
        outputImages: {
			1: '4kpro-crt-c.png',
			2: '1440-crt-c.png',
			3: '1080-crt-c.png',
			4: 'HDMI-YPBPR.png',
        },
    },

	
	
    // Add more matrix devices above this line
];
    