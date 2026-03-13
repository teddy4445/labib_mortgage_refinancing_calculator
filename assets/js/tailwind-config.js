window.tailwind = window.tailwind || {};
window.tailwind.config = {
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#ECF3FF",
          100: "#D9E7FF",
          200: "#B7D1FF",
          300: "#8DB4F5",
          400: "#5F8BE2",
          500: "#3568DC",
          600: "#123B6B",
          700: "#0F3158",
          800: "#0A2440",
          900: "#081726"
        },
        royal: {
          50: "#EEF4FF",
          100: "#DCE8FF",
          200: "#BBD0FF",
          300: "#8EAFFF",
          400: "#5E86F4",
          500: "#3568DC",
          600: "#2B56B5",
          700: "#21438E",
          800: "#183168",
          900: "#102243"
        },
        contrast: {
          50: "#FFF2E5",
          100: "#FFE2C7",
          200: "#FFC68F",
          300: "#F6A958",
          400: "#E98A2E",
          500: "#D97706",
          600: "#B86005",
          700: "#8E4908",
          800: "#6C380A",
          900: "#472607"
        },
        ink: "#1D2B3A",
        slateText: "#5B6675",
        surface: "#F6F8FB",
        line: "#D9E0E7",
        accent: "#D97706",
        success: "#178A4B",
        warning: "#C98A00",
        danger: "#B9382F"
      },
      boxShadow: {
        soft: "0 14px 34px rgba(18, 59, 107, 0.09)",
        panel: "0 22px 56px rgba(17, 37, 62, 0.12)"
      },
      borderRadius: {
        panel: "1.25rem"
      },
      fontFamily: {
        sans: ["Heebo", "ui-sans-serif", "system-ui", "sans-serif"]
      },
      maxWidth: {
        dashboard: "1280px"
      }
    }
  }
};
