import { useCallback, useEffect, useState } from 'react'
import {
  Badge, Box, Button, Container, Flex, Grid, GridItem, Heading, HStack, Spacer, Stack, Text, useToast,
} from '@chakra-ui/react'
import { getExtraction, getHealth, hasToken, setToken, setUnauthorizedHandler } from './api'
import LoginForm from './components/LoginForm'
import UploadPanel from './components/UploadPanel'
import HistoryList from './components/HistoryList'
import ResultsView from './components/ResultsView'
import EmptyState from './components/EmptyState'

export default function App() {
  const [authed, setAuthed] = useState(hasToken())
  const [health, setHealth] = useState(null)
  const [record, setRecord] = useState(null)
  const [fileUrl, setFileUrl] = useState(null) // object URL of the PDF just uploaded, for the preview tab
  const [historyKey, setHistoryKey] = useState(0)
  const toast = useToast()

  const logout = useCallback((expired = false) => {
    setToken(null)
    setAuthed(false)
    setRecord(null)
    if (expired) toast({ status: 'warning', title: 'Session expired, please log in again' })
  }, [toast])

  useEffect(() => { setUnauthorizedHandler(() => logout(true)) }, [logout])
  useEffect(() => { getHealth().then(setHealth).catch(() => setHealth({ status: 'down' })) }, [])

  const handleResult = (rec, file) => {
    if (fileUrl) URL.revokeObjectURL(fileUrl)
    setFileUrl(file ? URL.createObjectURL(file) : null)
    setRecord(rec)
    setHistoryKey((k) => k + 1)
  }

  const openFromHistory = async (id) => {
    try {
      const rec = await getExtraction(id)
      if (fileUrl) URL.revokeObjectURL(fileUrl)
      setFileUrl(null)
      setRecord(rec)
    } catch (e) {
      toast({ status: 'error', title: 'Could not load extraction', description: e.message })
    }
  }

  return (
    <Box minH="100vh">
      <Box as="header" bg="white" borderBottomWidth="1px" position="sticky" top={0} zIndex={10}>
        <Container maxW="7xl" py={3}>
          <Flex align="center" gap={3} wrap="wrap">
            <Box w={8} h={8} borderRadius="md" bg="brand.500" color="white" display="grid" placeItems="center"
                 fontWeight="bold" fontSize="sm">CA</Box>
            <Stack spacing={0}>
              <Heading size="sm">Clinical AI</Heading>
              <Text fontSize="xs" color="gray.500">Intelligent PDF extraction</Text>
            </Stack>
            <Spacer />
            {health && (
              <HStack spacing={2}>
                <Badge colorScheme={health.status === 'ok' ? 'green' : 'red'} variant="subtle">
                  API {health.status === 'ok' ? 'online' : 'offline'}
                </Badge>
                {health.model && <Badge variant="outline" textTransform="none">{health.model}</Badge>}
              </HStack>
            )}
            {authed && <Button size="sm" variant="ghost" colorScheme="gray" onClick={() => logout()}>Log out</Button>}
          </Flex>
        </Container>
      </Box>

      <Container maxW="7xl" py={6}>
        {!authed ? (
          <LoginForm onLoggedIn={() => setAuthed(true)} />
        ) : (
          <Grid templateColumns={{ base: '1fr', lg: '340px 1fr' }} gap={6} alignItems="start">
            <GridItem>
              <Stack spacing={6} position={{ lg: 'sticky' }} top={{ lg: '84px' }}>
                <UploadPanel onResult={handleResult} />
                <HistoryList refreshKey={historyKey} activeId={record?.id} onOpen={openFromHistory} />
              </Stack>
            </GridItem>
            <GridItem minW={0}>
              {record ? <ResultsView record={record} fileUrl={fileUrl} /> : <EmptyState />}
            </GridItem>
          </Grid>
        )}
      </Container>
    </Box>
  )
}
