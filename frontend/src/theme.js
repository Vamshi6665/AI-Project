import { extendTheme } from '@chakra-ui/react'

const theme = extendTheme({
  config: { initialColorMode: 'light', useSystemColorMode: false },
  colors: {
    brand: {
      50: '#e6f6f4', 100: '#c2e9e4', 200: '#99dad2', 300: '#6ccbc0', 400: '#45bfb2',
      500: '#1fa395', 600: '#178377', 700: '#11645b', 800: '#0b4640', 900: '#052825',
    },
  },
  fonts: {
    heading: `'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif`,
    body: `'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif`,
  },
  styles: { global: { body: { bg: 'gray.50' } } },
  components: {
    Button: { defaultProps: { colorScheme: 'brand' } },
    Tabs: { defaultProps: { colorScheme: 'brand' } },
  },
})

export default theme
