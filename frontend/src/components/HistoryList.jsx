import { useEffect, useState } from 'react'
import { Box, Card, CardBody, Heading, Stack, Text } from '@chakra-ui/react'
import { listExtractions } from '../api'

export default function HistoryList({ refreshKey, activeId, onOpen }) {
  const [items, setItems] = useState([])

  useEffect(() => {
    listExtractions().then(setItems).catch(() => setItems([]))
  }, [refreshKey])

  return (
    <Card>
      <CardBody>
        <Stack spacing={3}>
          <Heading size="sm">Recent extractions</Heading>
          {items.length === 0 && <Text fontSize="sm" color="gray.500">Nothing yet. Upload a PDF to start.</Text>}
          {items.map((it) => (
            <Box
              key={it.id}
              as="button"
              textAlign="left"
              onClick={() => onOpen(it.id)}
              p={3}
              borderRadius="md"
              borderWidth="1px"
              borderColor={it.id === activeId ? 'brand.400' : 'gray.200'}
              bg={it.id === activeId ? 'brand.50' : 'white'}
              _hover={{ borderColor: 'brand.300' }}
            >
              <Text fontSize="sm" fontWeight="medium" noOfLines={1}>{it.patient_name || 'Unknown patient'}</Text>
              <Text fontSize="xs" color="gray.500" noOfLines={1}>
                {it.document_type || 'document'} · {it.filename}
              </Text>
              <Text fontSize="xs" color="gray.400">{new Date(it.created_at).toLocaleString()} · {it.provider}</Text>
            </Box>
          ))}
        </Stack>
      </CardBody>
    </Card>
  )
}
