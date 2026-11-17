import {
  Alert, AlertIcon, Badge, Box, Button, Card, CardBody, Heading, HStack, List, ListItem, SimpleGrid, Stack,
  Tab, Table, TableContainer, TabList, TabPanel, TabPanels, Tabs, Tbody, Td, Text, Th, Thead, Tr, Wrap,
  useClipboard,
} from '@chakra-ui/react'
import { CopyIcon, DownloadIcon } from '@chakra-ui/icons'

const FLAG_COLORS = { high: 'red', low: 'orange', critical: 'purple', normal: 'green' }

function Field({ label, value }) {
  return (
    <Box>
      <Text fontSize="xs" color="gray.500" textTransform="uppercase" letterSpacing="wide">{label}</Text>
      <Text fontSize="sm" fontWeight="medium">{value || '—'}</Text>
    </Box>
  )
}

function Section({ title, children }) {
  return (
    <Card variant="outline">
      <CardBody>
        <Heading size="xs" textTransform="uppercase" color="gray.500" mb={3}>{title}</Heading>
        {children}
      </CardBody>
    </Card>
  )
}

function DataTable({ columns, rows, empty }) {
  if (!rows?.length) return <Text fontSize="sm" color="gray.500">{empty}</Text>
  return (
    <TableContainer borderWidth="1px" borderRadius="md">
      <Table size="sm">
        <Thead bg="gray.50">
          <Tr>{columns.map((c) => <Th key={c.key}>{c.label}</Th>)}</Tr>
        </Thead>
        <Tbody>
          {rows.map((row, i) => (
            <Tr key={i}>
              {columns.map((c) => (
                <Td key={c.key} whiteSpace="normal">{c.render ? c.render(row) : (row[c.key] ?? '—')}</Td>
              ))}
            </Tr>
          ))}
        </Tbody>
      </Table>
    </TableContainer>
  )
}

function BulletList({ items, empty }) {
  if (!items?.length) return <Text fontSize="sm" color="gray.500">{empty}</Text>
  return <List spacing={1} fontSize="sm">{items.map((x, i) => <ListItem key={i}>{'•'} {x}</ListItem>)}</List>
}

export default function ResultsView({ record, fileUrl }) {
  const { data, document: doc, inference, warnings } = record
  const json = JSON.stringify(record.data, null, 2)
  const { onCopy, hasCopied } = useClipboard(json)

  const download = () => {
    const blob = new Blob([json], { type: 'application/json' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = doc.filename.replace(/\.pdf$/i, '') + '.extraction.json'
    a.click()
    URL.revokeObjectURL(a.href)
  }

  const abnormalLabs = data.lab_results.filter((l) => l.flag && l.flag !== 'normal').length

  return (
    <Stack spacing={4}>
      <Card>
        <CardBody>
          <Stack spacing={3}>
            <HStack justify="space-between" align="start" wrap="wrap" gap={2}>
              <Stack spacing={0}>
                <Heading size="md">{data.patient.name || 'Unknown patient'}</Heading>
                <Text fontSize="sm" color="gray.500">{doc.filename}</Text>
              </Stack>
              <Wrap>
                {data.document_type && <Badge colorScheme="brand">{data.document_type}</Badge>}
                <Badge variant="outline" textTransform="none">{inference.model}</Badge>
                <Badge variant="subtle" textTransform="none">{(inference.latency_ms / 1000).toFixed(1)} s</Badge>
                <Badge variant="subtle" textTransform="none">{doc.pages} page{doc.pages === 1 ? '' : 's'}</Badge>
                {inference.attempts > 1 && <Badge colorScheme="yellow" textTransform="none">repaired on retry</Badge>}
              </Wrap>
            </HStack>
            {warnings.map((w) => (
              <Alert key={w} status="warning" variant="left-accent" fontSize="sm" py={2}><AlertIcon />{w}</Alert>
            ))}
          </Stack>
        </CardBody>
      </Card>

      <Card>
        <CardBody>
          <Tabs isLazy variant="soft-rounded" size="sm">
            <TabList overflowX="auto" pb={2} gap={1} sx={{ '& > button': { whiteSpace: 'nowrap', flexShrink: 0 } }}>
              <Tab>Overview</Tab>
              <Tab>Diagnoses ({data.diagnoses.length})</Tab>
              <Tab>Medications ({data.medications.length})</Tab>
              <Tab>Labs ({data.lab_results.length}){abnormalLabs > 0 && <Badge ml={1} colorScheme="red">{abnormalLabs}</Badge>}</Tab>
              <Tab>Vitals &amp; allergies</Tab>
              {fileUrl && <Tab>Document</Tab>}
              <Tab>JSON</Tab>
            </TabList>
            <TabPanels>
              <TabPanel px={0}>
                <Stack spacing={4}>
                  {data.summary && (
                    <Section title="Summary"><Text fontSize="sm">{data.summary}</Text></Section>
                  )}
                  <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                    <Section title="Patient">
                      <SimpleGrid columns={2} spacing={3}>
                        <Field label="Name" value={data.patient.name} />
                        <Field label="MRN" value={data.patient.mrn} />
                        <Field label="Date of birth" value={data.patient.date_of_birth} />
                        <Field label="Sex" value={data.patient.sex} />
                      </SimpleGrid>
                    </Section>
                    <Section title="Encounter">
                      <SimpleGrid columns={2} spacing={3}>
                        <Field label="Date" value={data.encounter.date} />
                        <Field label="Provider" value={data.encounter.provider} />
                        <Field label="Facility" value={data.encounter.facility} />
                        <Field label="Department" value={data.encounter.department} />
                      </SimpleGrid>
                    </Section>
                    <Section title="Procedures"><BulletList items={data.procedures} empty="None recorded" /></Section>
                    <Section title="Follow-up"><BulletList items={data.follow_up} empty="None recorded" /></Section>
                  </SimpleGrid>
                  <Section title="Social history">
                    <BulletList items={data.social_history ?? []} empty="None recorded" />
                  </Section>
                </Stack>
              </TabPanel>

              <TabPanel px={0}>
                <DataTable
                  empty="No diagnoses found"
                  rows={data.diagnoses}
                  columns={[
                    { key: 'description', label: 'Diagnosis' },
                    { key: 'icd10_code', label: 'ICD-10', render: (r) => r.icd10_code ? <Badge>{r.icd10_code}</Badge> : '—' },
                    { key: 'status', label: 'Status' },
                  ]}
                />
              </TabPanel>

              <TabPanel px={0}>
                <DataTable
                  empty="No medications found"
                  rows={data.medications}
                  columns={[
                    { key: 'name', label: 'Medication' },
                    { key: 'dose', label: 'Dose' },
                    { key: 'route', label: 'Route' },
                    { key: 'frequency', label: 'Frequency' },
                    { key: 'status', label: 'Status', render: (r) => r.status
                      ? <Badge colorScheme={r.status === 'new' ? 'blue' : r.status === 'discontinued' ? 'gray' : 'green'}>{r.status}</Badge>
                      : '—' },
                  ]}
                />
              </TabPanel>

              <TabPanel px={0}>
                <DataTable
                  empty="No lab results found"
                  rows={data.lab_results}
                  columns={[
                    { key: 'test', label: 'Test' },
                    { key: 'value', label: 'Value', render: (r) => <Text as="span" fontWeight="semibold">{r.value}</Text> },
                    { key: 'unit', label: 'Unit' },
                    { key: 'reference_range', label: 'Reference' },
                    { key: 'flag', label: 'Flag', render: (r) => r.flag
                      ? <Badge colorScheme={FLAG_COLORS[r.flag]}>{r.flag}</Badge> : '—' },
                  ]}
                />
              </TabPanel>

              <TabPanel px={0}>
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
                  <Section title="Vitals">
                    <DataTable empty="No vitals found" rows={data.vitals}
                      columns={[{ key: 'name', label: 'Vital' }, { key: 'value', label: 'Value' }, { key: 'unit', label: 'Unit' }]} />
                  </Section>
                  <Section title="Allergies">
                    {data.allergies.length
                      ? <Wrap>{data.allergies.map((a) => <Badge key={a} colorScheme="red" variant="subtle" textTransform="none" px={2} py={1}>{a}</Badge>)}</Wrap>
                      : <Text fontSize="sm" color="gray.500">No allergies recorded</Text>}
                  </Section>
                </SimpleGrid>
              </TabPanel>

              {fileUrl && (
                <TabPanel px={0}>
                  <Box as="iframe" src={fileUrl} title="Uploaded PDF" w="100%" h="75vh" borderWidth="1px" borderRadius="md" />
                </TabPanel>
              )}

              <TabPanel px={0}>
                <HStack mb={3}>
                  <Button size="sm" leftIcon={<CopyIcon />} variant="outline" onClick={onCopy}>{hasCopied ? 'Copied' : 'Copy'}</Button>
                  <Button size="sm" leftIcon={<DownloadIcon />} variant="outline" onClick={download}>Download</Button>
                </HStack>
                <Box as="pre" fontSize="xs" bg="gray.900" color="green.100" p={4} borderRadius="md" overflow="auto" maxH="70vh">
                  {json}
                </Box>
              </TabPanel>
            </TabPanels>
          </Tabs>
        </CardBody>
      </Card>
    </Stack>
  )
}
