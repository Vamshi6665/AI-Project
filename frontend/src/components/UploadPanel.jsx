import { useEffect, useRef, useState } from 'react'
import {
  Box, Button, Card, CardBody, Heading, HStack, Progress, Stack, Text, useToast,
} from '@chakra-ui/react'
import { AttachmentIcon } from '@chakra-ui/icons'
import { extractPdf } from '../api'

const MAX_MB = 10

export default function UploadPanel({ onResult }) {
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [phase, setPhase] = useState('idle') // idle | uploading | processing
  const [uploadPct, setUploadPct] = useState(0)
  const [elapsed, setElapsed] = useState(0)
  const inputRef = useRef(null)
  const toast = useToast()

  // Elapsed-seconds counter while the model runs.
  useEffect(() => {
    if (phase !== 'processing') return
    const started = Date.now()
    const id = setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 250)
    return () => clearInterval(id)
  }, [phase])

  const choose = (f) => {
    if (!f) return
    if (!f.name.toLowerCase().endsWith('.pdf')) {
      toast({ status: 'warning', title: 'Only PDF files are supported' })
      return
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      toast({ status: 'warning', title: `File is larger than ${MAX_MB} MB` })
      return
    }
    setFile(f)
  }

  const run = async () => {
    setPhase('uploading')
    setUploadPct(0)
    setElapsed(0)
    try {
      const record = await extractPdf(file, (pct) => {
        setUploadPct(pct)
        if (pct >= 100) setPhase('processing')
      })
      onResult(record, file)
      toast({ status: 'success', title: 'Extraction complete', duration: 2500 })
      setFile(null)
    } catch (e) {
      toast({
        status: 'error',
        title: e.message,
        description: e.requestId ? `${e.code} · request ${e.requestId}` : e.code,
        duration: 8000,
        isClosable: true,
      })
    } finally {
      setPhase('idle')
    }
  }

  const busy = phase !== 'idle'

  return (
    <Card>
      <CardBody>
        <Stack spacing={4}>
          <Heading size="sm">Upload a clinical PDF</Heading>
          <Box
            role="button"
            tabIndex={0}
            onClick={() => !busy && inputRef.current?.click()}
            onKeyDown={(e) => e.key === 'Enter' && !busy && inputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => { e.preventDefault(); setDragging(false); if (!busy) choose(e.dataTransfer.files?.[0]) }}
            borderWidth="2px"
            borderStyle="dashed"
            borderColor={dragging ? 'brand.400' : 'gray.300'}
            bg={dragging ? 'brand.50' : 'gray.50'}
            borderRadius="lg"
            p={6}
            textAlign="center"
            cursor={busy ? 'not-allowed' : 'pointer'}
            transition="all 0.15s"
            _hover={{ borderColor: busy ? undefined : 'brand.400' }}
          >
            <AttachmentIcon boxSize={6} color="brand.500" mb={2} />
            <Text fontWeight="medium">{file ? file.name : 'Drop a PDF here or click to browse'}</Text>
            <Text fontSize="xs" color="gray.500">
              {file ? `${(file.size / 1024).toFixed(0)} KB` : `Text-based PDF, up to ${MAX_MB} MB`}
            </Text>
            <input ref={inputRef} type="file" accept="application/pdf,.pdf" hidden
                   onChange={(e) => { choose(e.target.files?.[0]); e.target.value = '' }} />
          </Box>

          {phase === 'uploading' && (
            <Stack spacing={1}>
              <Text fontSize="xs" color="gray.600">Uploading {uploadPct}%</Text>
              <Progress value={uploadPct} size="sm" borderRadius="full" colorScheme="brand" />
            </Stack>
          )}
          {phase === 'processing' && (
            <Stack spacing={1}>
              <HStack justify="space-between">
                <Text fontSize="xs" color="gray.600">Extracting text and running the model</Text>
                <Text fontSize="xs" color="gray.500">{elapsed}s</Text>
              </HStack>
              <Progress isIndeterminate size="sm" borderRadius="full" colorScheme="brand" />
            </Stack>
          )}

          <Button onClick={run} isDisabled={!file || busy} isLoading={busy} loadingText="Processing">
            Extract data
          </Button>
        </Stack>
      </CardBody>
    </Card>
  )
}
